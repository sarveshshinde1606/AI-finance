from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include


from . import views

urlpatterns = [
    path('', views.index, name="home"),
    path('about/', views.about, name="about"),
    path('master/',views.master,name="master"),
   
    path('register/', views.register, name="register"),
    path('logout/', views.logout_view, name="logout"),
    path('login1/', views.login1, name="login1"),  
    path('admin/', admin.site.urls),
    path("learning/", views.learning_dashboard, name="learning"),
    path("gamification/", views.gamification_panel, name="gamification"),
    path("main_dashboard/", views.main_dashboard, name="main_dashboard"),

    path("quiz_panel/", views.quiz_panel, name="quiz_panel"),
    path("progress_dashboard/", views.progress_dashboard, name="progress_dashboard"),

    path("download-report/", views.download_progress_report, name="download_report"),
     path("budget_dashboard/", views.budget_dashboard, name="budget_dashboard"),

    # Personalized Budgeting
    path("personalized_budgeting/", views.personalized_budgeting, name="personalized_budgeting"),

    # # Investment Recommendation
    path("investment_recommendation/", views.investment_recommendation, name="investment_recommendation"),

    # # AI Assistant
    path("ai_assistant/", views.ai_assistant, name="ai_assistant"),

    # # Human Assistant
    path("human_assistant/", views.human_assistant, name="human_assistant"),
    # path('human-assistant/', views.human_assistant, name='human_assistant'),
    path('admin_panel/', views.custom_admin_dashboard, name='admin_panel'),
    path('proxy-scanner/', views.proxy_scanner, name='proxy_scanner'),

    # path('custom-admin/', views.admin_panel, name='admin_panel'),
    # path('update-request/<int:request_id>/', views.update_request_status, name='update_request_status'),
    path('custom_admin_login/', views.custom_admin_login, name='custom_admin_login'),
    path('custom_admin_dashboard/', views.custom_admin_dashboard, name='custom_admin_dashboard'),
    path('update-request/<int:request_id>/', views.update_request_status, name='update_request_status'),
    path('admin-logout/', views.custom_admin_logout, name='custom_admin_logout'),







    # path('learning_panel/', views.learning_panel, name='learning_panel'),  # Age 15–25 dashboard
    # path('planning_panel/', views.planning_panel, name='planning_panel'),
    # path('dashboard/', views.dashboard, name='dashboard'),
    # path('budget/', views.budget_planner, name='budget_planner'),
    
]

if settings.DEBUG:    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

