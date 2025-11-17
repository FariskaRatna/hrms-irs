def load_global_js(bootinfo):
    if "app_scripts" not in bootinfo:
        bootinfo["app_scripts"] = []
    bootinfo["app_scripts"].append("/assets/hrms/js/global_readonly.js")
