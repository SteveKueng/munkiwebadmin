from django.db import models
import plistlib
import base64
import bz2
import django

class Machine(models.Model):
    serial_number = models.CharField(max_length=16, unique=True, primary_key=True)
    hostname = models.CharField(max_length=64, blank=True)
    username = models.CharField(max_length=256, blank=True)
    remote_ip = models.CharField(max_length=15, blank=True)
    machine_model = models.CharField(max_length=64, blank=True)
    cpu_type = models.CharField(max_length=64, blank=True)
    cpu_speed = models.CharField(max_length=32, blank=True)
    cpu_arch = models.CharField(max_length=32, blank=True)
    ram = models.CharField(max_length=16, blank=True)
    os_version = models.CharField(max_length=16, blank=True)
    img_url = models.CharField(max_length=200, blank=True)

    def errors(self):
        return MunkiReport.objects.get(machine=self).errors
    
    def warnings(self):
        return MunkiReport.objects.get(machine=self).warnings

    def console_user(self):
        obj = MunkiReport.objects.get(machine=self)
        return obj.console_user

    def report_time(self):
        obj = MunkiReport.objects.get(machine=self)
        return obj.timestamp
        
    class Meta:
        ordering = ['hostname']

class MunkiReport(models.Model):
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='munkireport')
    timestamp = models.DateTimeField(default=django.utils.timezone.now)
    runtype = models.CharField(max_length=64)
    runstate = models.CharField(max_length=16)
    console_user = models.CharField(max_length=64)
    errors = models.IntegerField(default=0)
    warnings = models.IntegerField(default=0)
    activity = models.TextField(editable=False, null=True)
    report = models.TextField(editable=False, null=True)
    class Meta:
        ordering = ['machine']
        permissions = (("can_view_reports", "Can view reports"),
                       ("can_view_dashboard", "Can view dashboard"),
                       ("can_push_mdm", "Can push mdm"),)

    def hostname(self):
        return self.machine.hostname

    def encode(self, plist):
        string = plistlib.dumps(plist)
        bz2data = bz2.compress(string)
        b64data = base64.b64encode(bz2data)
        return b64data

    def decode(self, data):
        # this has some sucky workarounds for odd handling
        # of UTF-8 data in sqlite3
        try:
            plist = plistlib.readPlistFromString(data)
            return plist
        except:
            try:
                plist = plistlib.readPlistFromString(data.encode('UTF-8'))
                return plist
            except:
                try:
                    return self.b64bz_decode(data)
                except:
                    return dict()

    def b64bz_decode(self, data):
        try:
            bz2data = base64.b64decode(data)
            string = bz2.decompress(bz2data)
            plist = plistlib.loads(string)
            return plist
        except Exception:
            return {}

    def get_report(self):
        return self.b64bz_decode(self.report)

    def get_activity(self):
        return self.decode(self.activity)

    def update_report(self, base64bz2report):
        # Save report.
        try:
            #base64bz2report = base64bz2report.replace(" ", "+")
            plist = self.b64bz_decode(base64bz2report)
            self.report = base64bz2report
        except:
            plist = None
            self.report = ''

        if plist is None:
            self.activity = None
            self.errors = 0
            self.warnings = 0
            return

        # Check activity.
        activity = dict()
        for section in ("ItemsToInstall",
                        "InstallResults",
                        "ItemsToRemove",
                        "RemovalResults",
                        "AppleUpdates"):
            if (section in plist) and len(plist[section]):
                activity[section] = plist[section]
        if activity:
            self.activity = plistlib.dumps(activity)
        else:
            self.activity = None

        # Check errors and warnings.
        if "Errors" in plist:
            self.errors = len(plist["Errors"])
        else:
            self.errors = 0

        if "Warnings" in plist:
            self.warnings = len(plist["Warnings"])
        else:
            self.warnings = 0

        # Check console user.
        self.console_user = "unknown"
        if "ConsoleUser" in plist:
            self.console_user = plist["ConsoleUser"]
