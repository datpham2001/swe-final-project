import re
from django.shortcuts import render
from .models import *
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Count
from rest_framework import status
from django.conf import settings
import jwt
from .utils import *
import json

# Create your views here.

#sign up 
def signup(request):
  if request.method == 'POST':
    body_unicode = request.body.decode('utf-8') 	
    body = json.loads(body_unicode) 	
    username = body['username']
    password = body['password']
    role = body['role']
    
    if len(password) < 8:
      return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={'status': status.HTTP_403_FORBIDDEN, 'success': False, 'message': "Mật khẩu không hợp lệ"})
    
    user_obj = Account(username=username, password=password, role=role) 
    
    #if user not exist before
    if Account.objects.count() == 0:
      user_obj.role = 'admin'
    elif Account.objects.filter(username=user_obj.username).exists():
      return JsonResponse(status=status.HTTP_403_FORBIDDEN, data= {"status": status.HTTP_403_FORBIDDEN, 'success': False, "message": "Tên người dùng đã tồn tại"})
    elif (user_obj.role == "admin" and Account.objects.filter(role="admin").exists()):
      return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status": status.HTTP_403_FORBIDDEN, "success": False, 'message': "Đã tồn tại tài khoản admin"})
    
    #else success
    hashedPassword = make_password(user_obj.password)
    user_obj.password = hashedPassword
    user_obj.save()
    if user_obj.role == 'admin':
      return JsonResponse(status=status.HTTP_201_CREATED, data={"status": status.HTTP_201_CREATED, "success": True, "message": "Đăng kí admin thành công", "details" : {'username': user_obj.username, 'role': user_obj.role}})
    
    return JsonResponse(status=status.HTTP_201_CREATED, data={"status": status.HTTP_201_CREATED, "success": True, 'message': "Đăng kí người dùng thành công", 'details': {'username': user_obj.username, 'role': user_obj.role}})

#login 
def login(request):
  if request.method == 'POST':
    body_unicode = request.body.decode('utf-8') 	
    body = json.loads(body_unicode) 	
    username = body['username']
    password = body['password']

    user = Account.objects.get(username=username)
    if not user:
      return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status": status.HTTP_403_FORBIDDEN, "success": False, 'message': "Tên người dùng không tồn tại"})
    
    if check_password(password, user.password) == False:
      return JsonResponse(status=status.HTTP_403_FORBIDDEN, data= {"status": status.HTTP_403_FORBIDDEN, "success": False, 'message': "Tên đăng nhập/ Mật khẩu không đúng"})
    
   
    #user = auth.authenticate(username=username, password=password)
    auth_token = jwt.encode({'id': user.id}, settings.JWT_SECRET_KEY, algorithm="HS256")
    print(auth_token)
    data = {"username": user.username, "access-token": auth_token}
    return JsonResponse(status=status.HTTP_200_OK, data= {"status": status.HTTP_200_OK, "success": True, 'message': 'Đăng nhập thành công', 'details': data})  

def get_all_users(request):
  if request.method == 'GET':
    count = Account.objects.all().count()
    account_list = Account.objects.all().values('id', 'username', 'role')
    return JsonResponse(status=status.HTTP_200_OK, data={'status': status.HTTP_200_OK, 'success': True, 'result': list(account_list), 'total_users': count})

def get_user(request, id):
  if request.method == "GET":
    if not Account.objects.filter(pk=id).exists():
      return JsonResponse(status=status.HTTP_404_NOT_FOUND, data={'status': status.HTTP_404_NOT_FOUND, 'success': False, 'message': 'Tài khoản không tồn tại'})
    
    account = Account.objects.filter(pk=id).values('id', 'username', 'role')
    return JsonResponse(status=status.HTTP_200_OK, data={'status': status.HTTP_200_OK, 'success': True, 'detail': list(account)})
  
def update_account(request, id):
  if request.method == 'PUT':
    if not Account.objects.filter(pk=id).exists():
      return JsonResponse(status=status.HTTP_404_NOT_FOUND, data={'status': status.HTTP_404_NOT_FOUND, 'success': False, 'message': 'Tài khoản không tồn tại'})
  
    account = Account.objects.get(pk=id)
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    
    # must not change role admin
    if (account.role == 'admin' and body['role'] != 'admin'):
      for key, value in body.items():
        if key != 'role':
          setattr(account, key, value)
      account.save()
      return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={'status': status.HTTP_403_FORBIDDEN, 'success': False, 'message': 'Không thể thay đổi vai trò admin'})
    
    # must not change role to admin if admin is exist
    if (account.role != 'admin' and body['role'] == 'admin'):
      # check if admin is exist
      if Account.objects.filter(role='admin').exists():
        for key, value in body.items():
          if key != 'role':
            setattr(account, key, value)
        account.save()
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={'status': status.HTTP_403_FORBIDDEN, 'success': False, 'message': 'Admin đã tồn tại. Không thể có nhiều hơn 1 admin'})
      
    for key, value in body.items():
      setattr(account, key, value)
    account.save()
    return JsonResponse(status=status.HTTP_200_OK, data={'status': status.HTTP_200_OK, 'success': True, 'message': 'Cập nhật thành công'})

def delete_account(request, id):
  if request.method == 'DELETE':
    token = request.headers.get('x-access-token')
    ok, payload = verify_token(token)
    
    if ok:
      account = Account.objects.get(pk=payload['id'])
      if account.role != 'admin':
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status": status.HTTP_403_FORBIDDEN, "success": False, 'message': 'Không được cấp quyền thực hiện chức năng này'})
      
      if not Account.objects.filter(pk=id).exists():
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status": status.HTTP_403_FORBIDDEN, "success": False, 'message': 'Không tìm thấy tài khoản này'})
        
      del_account = Account.objects.get(pk=id)
      del_account.delete()
      if del_account.role == 'admin':
        return JsonResponse(status=status.HTTP_200_OK, data={"status": status.HTTP_200_OK, 'success': True, 'message': 'Hiện tại đã xóa tài khoản admin. Vui lòng thay thế bằng tài khoản khác'})
      
      return JsonResponse(status=status.HTTP_200_OK, data={"status": status.HTTP_200_OK, 'success': True, 'message': 'Xóa tài khoản thành công'})  
    
    return payload
  
'''CRUD API for Season'''
def create_season(request):
  if request.method == 'POST':
    token = request.headers.get('x-access-token')
    ok, payload = verify_token(token)
    
    if ok:
      account = Account.objects.get(pk=payload['id'])
      if account.role != 'admin':
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status": status.HTTP_403_FORBIDDEN, "success": False, 'message': 'Không được cấp quyền thực hiện chức năng này'})
      
      body_unicode = request.body.decode('utf-8') 	
      body = json.loads(body_unicode) 	

      # create season object
      name = body['name']
      logo = body['logo']
      start_date = body['start_date']
      end_date = body['end_date']
      max_numbers_of_teams = body['max_numbers_of_teams']
      rank = body['rank']
      reported_by = account
      season_obj = Season(name=name, logo=logo, start_date=start_date,end_date=end_date, max_numbers_of_teams= max_numbers_of_teams, rank = rank, reported_by=reported_by)
      
      if max_numbers_of_teams < 5:
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={'status': status.HTTP_403_FORBIDDEN, 'success': False, 'message': 'Chưa đủ điều kiện tạo giải đấu do số lượng đội bóng chưa đủ'})
      
      if (Season.objects.filter(name = season_obj.name).exists()):
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={'status': status.HTTP_403_FORBIDDEN, 'success': False, 'message': 'Mùa giải đã tồn tại'})
      
      data = {
        'status': status.HTTP_201_CREATED, 
        'success': True,
        'message': 'Tạo mùa giải thành công',
        'result': {
          "name": season_obj.name,
          "logo": season_obj.logo,
          "start_date": season_obj.start_date,
          "end_date": season_obj.end_date,
          "max_numbers_of_teams": season_obj.max_numbers_of_teams,
          "rank": season_obj.rank,
          "reported_by": season_obj.reported_by.username,
        }
      }
      
      season_obj.save()
      return JsonResponse(status=status.HTTP_201_CREATED, data=data)

    return payload
    
def update_season(request, id):
  if request.method == 'PUT':
    token = request.headers.get('x-access-token')
    ok, payload = verify_token(token)
    
    if ok:
      account = Account.objects.get(pk=payload['id'])
      if account.role != 'admin':
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status": status.HTTP_403_FORBIDDEN, "success": False, 'message': 'Không được cấp quyền thực hiện chức năng này'})
      
      body_unicode = request.body.decode('utf-8') 	
      body = json.loads(body_unicode) 	
      
      if not Season.objects.filter(pk=id).exists():
        return JsonResponse(status=status.HTTP_404_NOT_FOUND, data={'status': status.HTTP_404_NOT_FOUND, 'success': False, 'message': 'Không tìm thấy mùa giải'})

      if body['max_numbers_of_teams'] < 5:
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={'status': status.HTTP_403_FORBIDDEN, 'success': False, 'message': 'Chưa đủ điều kiện cập nhật giải đấu do số lượng đội bóng chưa đủ'})
      

      season = Season.objects.get(pk=id)
      for key, value in body.items():
        if key != 'id':
          setattr(season, key, value)
      season.save()
      data = {
        'status': status.HTTP_200_OK, 
        'success': True,
        'message': 'Cập nhật mùa giải thành công',
        'result': {
          "name": season.name,
          "logo": season.logo,
          "start_date": season.start_date,
          "end_date": season.end_date,
          "max_numbers_of_teams": season.max_numbers_of_teams,
          "rank": season.rank,
          "reported_by": season.reported_by.username,
        }
      }
      
      return JsonResponse(status=status.HTTP_200_OK, data=data)
    
    return payload

def get_all_seasons(request):
  if request.method == "GET":
    count = Season.objects.all().count()
    season_list = Season.objects.all().values()
    return JsonResponse(status=status.HTTP_200_OK, data={'status': status.HTTP_200_OK, 'success': True, 'result': list(season_list), 'total_seasons': count})
  
def get_season(request, id):
  if request.method == "GET":
    if not Season.objects.filter(pk=id).exists():
      return JsonResponse(status=status.HTTP_404_NOT_FOUND, data={'status': status.HTTP_404_NOT_FOUND, 'success': False, 'message': 'Mùa giải không tồn tại'})
    
    season = Season.objects.filter(pk=id).values()
    return JsonResponse(status=status.HTTP_200_OK, data={'status': status.HTTP_200_OK, 'success': True, 'detail': list(season)})
  
'''CRUD API for Team'''
def create_team(request):
  if request.method == 'POST':
    token = request.headers.get('x-access-token')
    ok, payload = verify_token(token)
    
    if ok:
      account = Account.objects.get(pk=payload['id'])
      if account.role != 'admin':
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status": status.HTTP_403_FORBIDDEN, "success": False, 'message': 'Không được cấp quyền thực hiện chức năng này'})
      
      body_unicode = request.body.decode('utf-8') 	
      body = json.loads(body_unicode) 	
      
      name = body['name']
      logo = body['logo']
      coach = body['coach']
      max_numbers_of_players = body['max_numbers_of_players']
      reported_by = account
      
      if max_numbers_of_players > 23:
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status":status.HTTP_403_FORBIDDEN, 'success': False, 'message': 'Số lượng đăng ký tối đa cầu thủ không được vượt quá 23 người'})
      
      if Team.objects.filter(name=name).exists():
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status":status.HTTP_403_FORBIDDEN, 'success': False, 'message': 'Đội bóng đã tồn tại'})
      
      if Team.objects.filter(coach=coach).exists():
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status":status.HTTP_403_FORBIDDEN, 'success': False, 'message': 'HLV đã thuộc của đội bóng khác'})
        
      team = Team(name=name, logo=logo, coach=coach, max_numbers_of_players=max_numbers_of_players, reported_by=reported_by)
      team.save()
      
      data = {
        'status': status.HTTP_201_CREATED, 
        'success': True,
        'message': 'Tạo đội bóng thành công',
        'result': {
          "name": team.name,
          "logo": team.logo,
          "max_numbers_of_teams": team.max_numbers_of_players,
          "reported_by": team.reported_by.username,
        }
      }
      
      return JsonResponse(status=status.HTTP_201_CREATED, data=data)
    return payload
  
def get_all_teams(request):
  if request.method == 'GET':
    count = Team.objects.all().count()
    team_list = Team.objects.all().values()
    
    return JsonResponse(status=status.HTTP_200_OK, data={'status': status.HTTP_200_OK, 'success': True, 'result': list(team_list), 'total_teams': count})
  
def get_team(request, id):
  if request.method == 'GET':
    if not Team.objects.filter(pk=id).exists():
      return JsonResponse(status=status.HTTP_404_NOT_FOUND, data={'status': status.HTTP_404_NOT_FOUND, 'success': False, 'message': 'Đội bóng không tồn tại'})
    
    team = Team.objects.filter(pk=id).values()
    return JsonResponse(status=status.HTTP_200_OK, data={'status': status.HTTP_200_OK, 'success': True, 'detail': list(team)})
  
def update_team(request, id):
  if request.method == 'PUT':
    token = request.headers.get('x-access-token')
    ok, payload = verify_token(token)
    
    if ok:
      account = Account.objects.get(pk=payload['id'])
      if account.role != 'admin':
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status": status.HTTP_403_FORBIDDEN, "success": False, 'message': 'Không được cấp quyền thực hiện chức năng này'})
      
      body_unicode = request.body.decode('utf-8') 	
      body = json.loads(body_unicode)
      
      if not Team.objects.filter(pk=id).exists():
        return JsonResponse(status=status.HTTP_404_NOT_FOUND, data={'status': status.HTTP_404_NOT_FOUND, 'success': False, 'message': 'Không tìm thấy mùa giải'})

      if body['max_numbers_of_players'] > 23:
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status":status.HTTP_403_FORBIDDEN, 'success': False, 'message': 'Số lượng đăng ký tối đa cầu thủ không được vượt quá 23 người'})
      
      team = Team.objects.get(pk=id)
      for key, value in body.items():
        if key != 'id':
          setattr(team, key, value)
      team.save()
      
      data = {
        'status': status.HTTP_200_OK, 
        'success': True,
        'message': 'Cập nhật đội bóng thành công',
        'result': {
          "name": team.name,
          "logo": team.logo,
          "coach": team.coach,
          "max_numbers_of_players": team.max_numbers_of_players,
          "reported_by": team.reported_by.username,
        }
      }
      
      return JsonResponse(status=status.HTTP_200_OK, data=data)
    
    return payload
  
'''CRUD API for player'''
def create_player(request):
  if request.method == 'POST':
    token = request.headers.get('x-access-token')
    ok, payload = verify_token(token)
    
    if ok:
      account = Account.objects.get(pk=payload['id'])
      if account.role != 'admin':
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status": status.HTTP_403_FORBIDDEN, "success": False, 'message': 'Không được cấp quyền thực hiện chức năng này'})
      
      body_unicode = request.body.decode('utf-8') 	
      body = json.loads(body_unicode) 
      
      name = body['name']
      image = body['image']
      age = body['age']
      gender = body['gender']
      height = body['height']
      weight = body['weight']
      position = body['position']
      point = body['point']
      added_by = Team.objects.get(pk=body['added_by'])
      
      player = Player(name=name, image=image, age=age, gender=gender, height=height, weight=weight, position=position, point=point, added_by=added_by, reported_by=account)
      player.save()
      data = {
       'status': status.HTTP_201_CREATED,
       'success': True,
       'message': 'Tạo cầu thủ thành công',
       'result': {
         'name': player.name,
         'age': player.age,
         'gender': player.gender,
         'position': player.position,
         'point': player.point,
         'added_by': player.added_by.id,
         'reported_by': account.username,
       } 
      }
      
      return JsonResponse(status=status.HTTP_201_CREATED, data=data)
    return payload
  
def get_all_players(request):
  if request.method == 'GET':
    count = Player.objects.all().count()
    player_list = Player.objects.all().values()
    
    return JsonResponse(status=status.HTTP_200_OK, data={'status': status.HTTP_200_OK, 'success': True, 'result': list(player_list), 'total_teams': count})
  
def get_player(request, id):
  if request.method == 'GET':
    if not Team.objects.filter(pk=id).exists():
      return JsonResponse(status=status.HTTP_404_NOT_FOUND, data={'status': status.HTTP_404_NOT_FOUND, 'success': False, 'message': 'Đội bóng không tồn tại'})
    
    team = Team.objects.filter(pk=id).values()
    return JsonResponse(status=status.HTTP_200_OK, data={'status': status.HTTP_200_OK, 'success': True, 'detail': list(team)})

def update_player(request, id):
  if request.method == 'PUT':
    token = request.headers.get('x-access-token')
    ok, payload = verify_token(token)
    
    if ok:
      account = Account.objects.get(pk=payload['id'])
      if account.role != 'admin':
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status": status.HTTP_403_FORBIDDEN, "success": False, 'message': 'Không được cấp quyền thực hiện chức năng này'})
    
      if not Player.objects.filter(pk=id).exists():
        return JsonResponse(status=status.HTTP_404_NOT_FOUND, data={'status': status.HTTP_404_NOT_FOUND, 'success': False, 'message': 'Không tìm thấy cầu thủ'})

      body_unicode = request.body.decode('utf-8') 	
      body = json.loads(body_unicode) 
      
      player = Player.objects.get(pk=id)
      for key, value in body.items():
        if key != 'id':
          setattr(player, key, value)
      player.save()
      
      data = {
        'status': status.HTTP_200_OK,
        'success': True,
        'message': 'Cập nhật cầu thủ thành công', 
        'result': {
          "name" : player.name,
          "image" : player.image, 
          "age" : player.age,
          "gender" : player.gender,
          "height" : player.height,
          "weight" : player.weight,
          "position" : player.position,
          "point" : player.point,
          "added_by" : player.added_by.name,
          "reported_by" : player.reported_by.username
        }
      }
      
      return JsonResponse(status=status.HTTP_200_OK, data=data)
    
    return payload

'''API for season detail'''
def create_season_team(request):
  if request.method == 'POST':
    token = request.headers.get('x-access-token')
    ok, payload = verify_token(token)
    
    if ok:
      account = Account.objects.get(pk=payload['id'])
      if account.role != 'admin':
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status": status.HTTP_403_FORBIDDEN, "success": False, 'message': 'Không được cấp quyền thực hiện chức năng này'})
      
      body_unicode = request.body.decode('utf-8') 	
      body = json.loads(body_unicode) 
      team_id = body['team_id']
      season_id = body['season_id']
      
      if not Season.objects.filter(pk=season_id).exists():
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={'status': status.HTTP_403_FORBIDDEN, 'success': False, 'message': 'Không tồn tại mùa giải này'})
      
      if not Team.objects.filter(pk=team_id).exists():
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={'status': status.HTTP_403_FORBIDDEN, 'success': False, 'message': 'Không tìm thấy đội bóng này'})
      
      team = Team.objects.get(pk=team_id)
      season = Season.objects.get(pk=season_id)
      season_detail = Season_Detail(season=season, team=team, reported_by=account, total_points=0)      
      season_detail.save()
      
      return JsonResponse(status=status.HTTP_200_OK, data={'status': status.HTTP_200_OK, 'success': True, 'message': 'Tạo đội bóng cho mùa giải thành công'})
    
    return payload

'''API for utils'''
def count_players_of_team(request, id):
  if request.method == 'GET':
    if not Team.objects.filter(pk=id).exists():
      return JsonResponse(status=status.HTTP_404_NOT_FOUND, data={'status': status.HTTP_404_NOT_FOUND, 'success': False, 'message': 'Không tìm thấy đội bóng'})
    
    team = Team.objects.get(pk=id)
    player_count = Player.objects.filter(added_by=team.id).count()
    
    return JsonResponse(status=status.HTTP_200_OK, data={'status': status.HTTP_200_OK, 'success': True, 'message': 'Query thành công', 'result': {'team': team.name, 'total_players': player_count}})

'''API for create match'''
def create_match(request):
  if request.method == 'POST':
    token = request.headers.get('x-access-token')
    ok, payload = verify_token(token)
    
    if ok:
      account = Account.objects.get(pk=payload['id'])
      if account.role != 'admin':
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={"status": status.HTTP_403_FORBIDDEN, "success": False, 'message': 'Không được cấp quyền thực hiện chức năng này'})
      
      body_unicode = request.body.decode('utf-8')
      body = json.loads(body_unicode)
      
      if not Season.objects.filter(pk=body['season_id']).exists():
        return JsonResponse(status=status.HTTP_404_NOT_FOUND, data={'status': status.HTTP_404_NOT_FOUND, 'success': False, 'message': 'Mùa giải không tồn tại'})
      
      if not Team.objects.filter(pk=body['team_1_id']).exists() or not Team.objects.filter(pk=body['team_2_id']).exists():
        return JsonResponse(status=status.HTTP_404_NOT_FOUND, data={'status': status.HTTP_404_NOT_FOUND, 'success': False, 'message': 'Không tìm thấy đội bóng'})
      
      if body['team_1_id'] == body['team_2_id']:
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={'status': status.HTTP_403_FORBIDDEN, 'success': False, 'message': 'Không thể tạo trấn đấu cho 1 đội bóng'})
      
      # two team must not meet exceed one time
      if Match.objects.filter(season_id=body['season_id'], first_team_id=body['team_1_id'], second_team_id=body['team_2_id']).exists() or Match.objects.filter(season_id=body['season_id'], first_team_id=body['team_2_id'], second_team_id=body['team_1_id']).exists():
        return JsonResponse(status=status.HTTP_403_FORBIDDEN, data={'status': status.HTTP_403_FORBIDDEN, 'success': False, 'message': 'Trận đấu đã tồn tại'})
      
      season = Season.objects.get(pk=body['season_id'])
      team_1 = Team.objects.get(pk=body['team_1_id'])
      team_2 = Team.objects.get(pk=body['team_2_id'])
      
      match = Match(season=season, first_team=team_1, second_team=team_2, result=body['result'])
      match.save()
      
      # update point for team in the season
      season_detail_team_1 = Season_Detail.objects.get(season=season, team=team_1)
      season_detail_team_2 = Season_Detail.objects.get(season=season, team=team_2)

      point_team_1, point_team_2 = match.result.split('-')
      if int(point_team_1) == int(point_team_2):
        season_detail_team_1.total_points += 1
        season_detail_team_2.total_points += 1
      elif int(point_team_1) > int(point_team_2):
        season_detail_team_1.total_points += 3
      else:
        season_detail_team_2.total_points += 3
        
      season_detail_team_1.save()
      season_detail_team_2.save()
      
      # update rank in the season
      season_detail = Season_Detail.objects.filter(season_id=season.id)
      season_team_detail = list(season_detail.values('team_id').order_by('-total_points').values('team_id'))
      
      rank = []
      for value in season_team_detail:
        team = Team.objects.get(pk=value['team_id'])
        rank.append(team.name)
      
      season.rank = rank
      season.save()
      
      data = {
        'status': status.HTTP_201_CREATED,
        'success': True,
        'message': 'Tạo trận đấu thành công', 
        'result': {
          'season_id': match.season.name,
          'team_1_id': match.first_team.name,
          'team_2_id': match.second_team.name,
          'result': match.result,          
        }
      }
      
      result = list(season_detail.values('season_id').annotate(dcount=Count('team_id')).values('dcount'))[0]['dcount']
      if Match.objects.filter(season_id=season.id).count() == calc_combination(result, 2) :
        data['note'] = 'Mùa giải kết thúc (đã thi đấu đủ số trận)'
              
      return JsonResponse(status=status.HTTP_201_CREATED, data=data)
    return payload

def delete_all(request):
  if request.method == 'DELETE':
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    Match.objects.filter(first_team_id=body['first_team_id'], second_team_id=body['second_team_id']).delete()  
    #Season_Detail.objects.filter(season_id=1).update(total_points=0)
    return JsonResponse(data={'status': status.HTTP_200_OK})
  
def home(request):
  if request.method == 'GET':
    return JsonResponse(status=status.HTTP_200_OK, data={'status': status.HTTP_200_OK, 'success': True, 'message': 'Server sẵn sàng lắng nghe...'})