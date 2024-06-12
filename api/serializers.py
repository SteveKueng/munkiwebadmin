from rest_framework.serializers import ModelSerializer
from reports.models import Machine, MunkiReport
from manifests.models import ManifestFile
from rest_framework import serializers

class MunkiReportDetailSerializer(ModelSerializer):
    runtype = serializers.CharField(read_only=True)
    runstate = serializers.CharField(read_only=True)
    console_user = serializers.CharField(read_only=True)
    class Meta:
        model = MunkiReport
        fields = [
            'timestamp',
            'runtype',
            'runstate',
            'console_user',
            'errors',
            'warnings',
            'activity',
            'report',
        ]
        read_only_fields = ('runtype', 'runstate', 'console_user')

class MachineListSerializer(ModelSerializer):
    class Meta:
        model = Machine
        fields = [
            'serial_number',
            'hostname',
            'os_version',
            'machine_model',
        ]

class MachineDetailSerializer(ModelSerializer):
    munkireport = MunkiReportDetailSerializer()
    class Meta:
        model = Machine
        fields = [
            'serial_number',
            'hostname',
            'username',
            'remote_ip',
            'machine_model',
            'cpu_type',
            'cpu_speed',
            'cpu_arch',
            'ram',
            'os_version',
            'img_url',
            'munkireport',
        ]
        #read_only_fields = ('munkireport',)
        depth = 1

class ManifestSerializer(ModelSerializer):
    managed_installs = serializers.ListField(child=serializers.CharField(), required=False)
    managed_uninstalls = serializers.ListField(child=serializers.CharField(), required=False)
    optional_installs = serializers.ListField(child=serializers.CharField(), required=False)
    included_manifests = serializers.ListField(child=serializers.CharField(), required=False)
    display_name = serializers.CharField(required=False, allow_blank=True)
    class Meta:
        model = ManifestFile
        fields = [
            'managed_installs',
            'managed_uninstalls',
            'optional_installs',
            'included_manifests',
            'display_name'
        ]