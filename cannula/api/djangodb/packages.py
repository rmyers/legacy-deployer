
from django.db.models.loading import get_model

from cannula.api.base.packages import PackageAPIBase

Package = get_model('cannula', 'package')


class PackageAPI(PackageAPIBase):
    
    
    def _get(self, package):
        if isinstance(package, Package):
            return package
        try:
            return Package.objects.get(name=package)
        except Package.DoesNotExist:
            # maybe an interger was passed
            pkg_pk = int(package)
            return Package.objects.get(pk=pkg_pk)
    
    
    def _list(self, user=None):
        if user and user.is_superuser:
            return Package.objects.all()
        return Package.objects.exclude(status__in=['admin', 'dep', 'inactive'])

    
    
    def _create(self, package, **kwargs):
        return Package.objects.create(name=package, **kwargs)