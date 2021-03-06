from django.urls import path
from . import views

urlpatterns = [
    path('', views.home),
    path('signup', views.signup, name='signup'),
    path('login', views.login, name='login'),
    path('users', views.get_all_users, name='get-all-users'),
    path('user/<id>', views.get_user, name='get-user'),
    path('change-account/<id>', views.update_account, name='change-account'),
    
    path('delete-account/<id>', views.delete_account, name='delete-account'),
    path('season', views.create_season, name='create-season'),
    path('season/<id>', views.update_season, name='update-season'),
    path('seasons', views.get_all_seasons, name='get-all-seasons'),
    path('season/<id>', views.get_season, name='get-season'),
    
    path('team', views.create_team, name='create-team'),
    path('teams', views.get_all_teams, name='get-all-teams'),
    path('team/<id>', views.get_team, name='get-team'),
    path('team/<id>', views.update_team, name='update-team'),
    path('import-team', views.create_season_team, name='import-team'),
    
    path('player', views.create_player, name='create-player'),
    path('player<id>', views.update_player, name='update-player'),
    path('players', views.get_all_players, name='get-all-players'),
    path('players/<id>', views.get_player, name='get-player'),
    
    path('team/count_players/<id>', views.count_players_of_team, name='count-players'),
    path('create-match', views.create_match, name='create-match'),
    path('delete', views.delete_all)
]