#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AbsenteismoController - App Desktop
Abre o sistema no navegador em modo app
"""
import subprocess
import os
import sys

chrome_paths = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
]

url = "https://www.absenteismocontroller.com.br/landing"

# Tenta abrir no Chrome em modo app
for chrome_path in chrome_paths:
    if os.path.exists(chrome_path):
        subprocess.Popen([chrome_path, f"--app={url}", "--new-window"])
        sys.exit(0)

# Se Chrome não encontrado, abre no navegador padrão
os.startfile(url)



