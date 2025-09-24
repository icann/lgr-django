from django.urls import path

from lgr_renderer import views

urlpatterns = [
    path('html/<lgr_model:model>/<int:lgr_pk>', views.LGRRendererView.as_view(), name='lgr_render'),
    path('file/<lgr_model:model>/<int:lgr_pk>', views.LGRDisplayView.as_view(), name='lgr_display'),
    path('dl/<lgr_model:model>/<int:lgr_pk>', views.LGRDisplayView.as_view(), name='lgr_download',
         kwargs={'force_download': True}),
]
