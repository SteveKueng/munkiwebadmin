#!/usr/bin/env python

import py_compile
import os
import stat

def replaceDataInFile(dataDict, filePath, replacedFile):
    orgFile = open(filePath, "r")
    fileData = orgFile.read()
    orgFile.close()
    for key, value in dataDict.iteritems():
        fileData = fileData.replace("{"+key+"}", value)
    orgFile = open(replacedFile, "w")
    orgFile.write(fileData)
    orgFile.close()

def main():
    path = os.path.dirname(os.path.realpath(__file__))
    preflight_script = path+'/preflight'
    postflight_script = path+'/postflight'
    report_broken_client_script = path+'/report_broken_client'

    preflight_script_final = path+'/payload/preflight.d/preflight_submit.py'
    postflight_script_final = path+'/payload/postflight.d/postflight_submit.py'
    report_broken_client_script_final = path+'/payload/report_broken_client.d/report_broken_client.py'

    preflight_script_repl = preflight_script + "_repl"
    postflight_script_repl = postflight_script + "_repl"
    report_broken_client_script_repl = report_broken_client_script + "_repl"

    mwa_host = raw_input("Please enter MWA (http://localhost:8080): ")
    user = raw_input("Please enter a report user: ")
    password = raw_input("Please enter a password for the report user: ")

    loginData = {'user': user, 'password': password, 'mwa': mwa_host }
    replaceDataInFile(loginData, preflight_script, preflight_script_repl)
    replaceDataInFile(loginData, postflight_script, postflight_script_repl)
    replaceDataInFile(loginData, report_broken_client_script, report_broken_client_script_repl)

    py_compile.compile(preflight_script_repl, preflight_script_final)
    py_compile.compile(postflight_script_repl, postflight_script_final)
    py_compile.compile(report_broken_client_script_repl, report_broken_client_script_final)

    st = os.stat(preflight_script_final)
    os.chmod(preflight_script_final, st.st_mode | stat.S_IEXEC)
    st = os.stat(postflight_script_final)
    os.chmod(postflight_script_final, st.st_mode | stat.S_IEXEC)
    st = os.stat(report_broken_client_script_final)
    os.chmod(report_broken_client_script_final, st.st_mode | stat.S_IEXEC)

    os.remove(preflight_script_repl)
    os.remove(postflight_script_repl)
    os.remove(report_broken_client_script_repl)

if __name__ == "__main__":
    main()