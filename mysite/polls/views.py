from django.shortcuts import render

from django.http import HttpResponse

from string import Template

latest_event = "No data yet"
on_time = ""
elapsed_time = ""
temperature = "No data yet"

def index(request):
    thePage = Template("    <style>" + \
    "  h1 { text-align: center; }" + \
    "  h3 { text-align: center; }" + \
    "</style>" + \
    "<h3>" + \
    "    Burner indicator light<br>" + \
    "    <i><big><big>" + \
    "        $latest_event" + \
    "        <br>" + \
    "        $on_time" + \
    "        <br>" + \
    "        $elapsed_time" + \
    "    </big></big></i>" + \
    "</h3>" + \
    "<h3>" + \
    "    Stovetop average temperature<br>" + \
    "    <i><big><big>" + \
    "        $temperature" + \
    "    </big></big></i>" + \
    "</h3>")
    return HttpResponse(thePage.substitute(latest_event = latest_event, on_time = on_time, 
                                           elapsed_time = elapsed_time, temperature = temperature))
