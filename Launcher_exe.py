from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import subprocess
import os
import requests
import zipfile
import json
import hashlib
import re

class Area_trabajo(QtCore.QObject):
    
    barra_progreso = QtCore.pyqtSignal(int)
    final_trabajo = QtCore.pyqtSignal()
    enviar_mensaje = QtCore.pyqtSignal(str)
    enviar_mensaje_cantidad_archivos = QtCore.pyqtSignal(str)
    activar_play = QtCore.pyqtSignal(bool)
    modo_ventana = QtCore.pyqtSignal(bool)
    activar_desactivar_modo_ventana = QtCore.pyqtSignal(bool)
    
    def main(self):
        
        #0 VERIFICACIÓN Y CONFIGURACIÓN DE CONFIG.INI
        
        self.activar_desactivar_modo_ventana.emit(False)
        
        try:
            
            with open("Config.ini","r") as config:
            
                lineas = config.readlines()
                
            for linea in lineas:
                
                if re.findall("WINMODE", linea):
                    
                    valor_bool = re.findall("WINMODE=(.)", linea)[0]
                    
                    self.modo_ventana.emit(bool(int(valor_bool)))
                    
                    break
            
        except Exception:
            
            self.modo_ventana.emit(False)
            
            with open("Config.ini","w") as config:
                
                config.write("[Config]\n"+"WINMODE=0\n")
        
        self.enviar_mensaje_cantidad_archivos.emit("")
        self.enviar_mensaje.emit("Descargando datos...")
        contenido_zip = "content.json.zip"
        url_content = "http://audl.axeso5.com/update/index/"+contenido_zip
        
        #1 DESCARGAR ARCHIVO CONTENT.JSON.ZIP
        
        try:
            archivo = requests.get(url_content, stream = True)
            peso_archivo = archivo.headers.get("Content-Length")
            division_archivo = 1    #comienza en 1 para que termine en 100
            parte_archivo = 0
        
        except Exception:
            self.enviar_mensaje.emit("Error de conexión.")
            self.final_trabajo.emit()
            return
            
        try:
            
            with open(contenido_zip,"wb") as content_json:
                
                for partes in archivo.iter_content(chunk_size=1):
                    content_json.write(partes)
                    parte_archivo += 1
                    
                    if (parte_archivo*100)/int(peso_archivo) >= division_archivo:
                        
                        self.barra_progreso.emit(division_archivo)
                        #print(division_archivo)
                        division_archivo += 1
            
            self.enviar_mensaje.emit("Descarga Finalizada.")
            
        except Exception:
            
            self.enviar_mensaje.emit("Error de descarga.")
            self.final_trabajo.emit()
            return
        
        #2 EXTRAER EL ARCHIVO CONTENT.JSON DE CONTENT.JSON.ZIP
        
        with zipfile.ZipFile(contenido_zip,"r") as file_content:
            contenido_json = file_content.namelist()[0] #nombre del archivo contenido
            file_content.extractall() #extraer archivos
        
        os.remove(contenido_zip)
        
        #3 OBTENER NOMBRES Y DATOS DE CONTENT.JSON
        
        with open(contenido_json,"r") as file:
            
            dic_contenido_json = json.load(file)
            archivos_audition = dic_contenido_json["files"]
            #print(archivos_audition)
        
        os.remove(contenido_json)
        
        #4 LECTURA Y VERIFICACIÓN DE ARCHIVOS PARA ACTUALIZAR
        
        lista_archivos_actualizar =[]
        
        cantidad_archivos_actualizar = [0,0]
        
        for archivo in archivos_audition:
            
            self.enviar_mensaje.emit("Comprobando "+archivo["localName"])
            
            try:
            
                with open(archivo["localName"],"rb") as f:
                    
                    if re.findall(".zip", archivo["remoteName"]):
                        
                        md5 = hashlib.md5()
                        
                        for partes in iter(lambda: f.read(4096),b""):
                            
                            md5.update(partes)
                            
                        local_hash_md5 = md5.hexdigest()
                        
                        if local_hash_md5 != archivo["localMd5"]:
                            
                            lista_archivos_actualizar.append([archivo["remoteName"],archivo["localName"]])
                            
                            cantidad_archivos_actualizar[1] += 1
                            
                    else:
                        
                        f.seek(0,os.SEEK_END)
                        
                        tamano_archivo = f.tell()
                        
                        if tamano_archivo != int(archivo["remoteSize"]):
                            
                            lista_archivos_actualizar.append([archivo["remoteName"],archivo["localName"]])
                            
                            cantidad_archivos_actualizar[1] += 1
                            
            except Exception:
                
                lista_archivos_actualizar.append([archivo["remoteName"],archivo["localName"]])
            
                cantidad_archivos_actualizar[1] += 1
        
        #print(lista_archivos_actualizar)
        
        #5 ACTUALIZACIÓN DE ARCHIVOS
        
        url_archivos = "http://audl.axeso5.com/update/content/"
        
        for cada_archivo in lista_archivos_actualizar:
            
            self.enviar_mensaje.emit("Descargando "+cada_archivo[0])
            
            cantidad_archivos_actualizar[0] += 1
            
            mensaje_cantidad_archivos_actualizar = str(cantidad_archivos_actualizar[0])+"/"+str(cantidad_archivos_actualizar[1])
            
            self.enviar_mensaje_cantidad_archivos.emit(mensaje_cantidad_archivos_actualizar)
            
            self.barra_progreso.emit(0)
            
            url_descarga = url_archivos+cada_archivo[0]
            
            try:
                
                descarga = requests.get(url_descarga, stream = True)
                peso_archivo = descarga.headers.get("Content-Length")
                division_archivo = round(int(peso_archivo)/100)
                parte_archivo_descargado = 0
                
            except Exception:
            
                self.enviar_mensaje.emit("Error de conexción.")
                self.final_trabajo.emit()
                return
            
            try:
                
                ruta_archivo = os.path.join(os.getcwd(),cada_archivo[0])
                ruta_archivo = os.path.dirname(ruta_archivo)
                
                #print(ruta_archivo)
                
                if not os.path.isdir(ruta_archivo):
                    
                    #print("No existe")
                    os.mkdir(ruta_archivo)
                
                with open(cada_archivo[0],"wb") as f:
                    
                    for partes in descarga.iter_content(chunk_size=division_archivo):
                        f.write(partes)
                        parte_archivo_descargado += division_archivo
                        
                        if division_archivo > int(peso_archivo):
                            
                            division_archivo = int(peso_archivo)
                            
                        dato_barra = round((parte_archivo_descargado*100)/int(peso_archivo))
                        self.barra_progreso.emit(dato_barra)
                        
                            
                if re.findall(".zip", cada_archivo[0]):
                    
                    with zipfile.ZipFile(cada_archivo[0],"r") as zip_file:
                        zip_file.extractall(ruta_archivo)
                        
                    os.remove(cada_archivo[0])
                            
            except Exception:
              
                self.enviar_mensaje.emit("Error de descarga.")
                self.final_trabajo.emit()
                return
         
        self.activar_desactivar_modo_ventana.emit(True)
        self.enviar_mensaje_cantidad_archivos.emit("")
        self.enviar_mensaje.emit("Listo para inicar el juego.")
        self.activar_play.emit(True)
        """for x in range(100):
            
            time.sleep(0.1)
            self.barra_progreso.emit(x+1)
            #print(x+1)
            
        self.enviar_mensaje.emit("Datos descargados.")"""
        self.final_trabajo.emit()
        

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(650, 210)
        MainWindow.setFixedSize(650, 210)
        
        icon = QtGui.QIcon()
        path = self.obtener_path()
        icon.addPixmap(QtGui.QPixmap(path+"/ico.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        self.boton_play = QtWidgets.QPushButton(self.centralwidget)
        self.boton_play.setEnabled(False)
        self.boton_play.setGeometry(QtCore.QRect(520, 40, 100, 100))
        self.boton_play.setObjectName("boton_play")
        
        self.barra = QtWidgets.QProgressBar(self.centralwidget)
        self.barra.setGeometry(QtCore.QRect(30, 140, 451, 23))
        self.barra.setProperty("value", 0)
        self.barra.setObjectName("barra")
        
        self.text = QtWidgets.QLabel(self.centralwidget)
        self.text.setGeometry(QtCore.QRect(30, 100, 341, 31))
        font = QtGui.QFont()
        font.setPointSize(8)
        self.text.setFont(font)
        self.text.setObjectName("text")
        
        self.n_archivos = QtWidgets.QLabel(self.centralwidget)
        self.n_archivos.setGeometry(QtCore.QRect(380, 100, 61, 31))
        self.n_archivos.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter)
        self.n_archivos.setObjectName("n_archivos")
        
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setGeometry(QtCore.QRect(0, 180, 651, 3))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        
        self.desarrollador = QtWidgets.QLabel(self.centralwidget)
        self.desarrollador.setGeometry(QtCore.QRect(30, 187, 111, 16))
        self.desarrollador.setObjectName("desarrollador")
        
        self.line_2 = QtWidgets.QFrame(self.centralwidget)
        self.line_2.setGeometry(QtCore.QRect(30, 20, 3, 70))
        self.line_2.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        
        self.line_3 = QtWidgets.QFrame(self.centralwidget)
        self.line_3.setGeometry(QtCore.QRect(30, 90, 440, 3))
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        
        self.line_4 = QtWidgets.QFrame(self.centralwidget)
        self.line_4.setGeometry(QtCore.QRect(470, 20, 3, 70))
        self.line_4.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_4.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_4.setObjectName("line_4")
        
        self.url_fb = QtWidgets.QLabel(self.centralwidget)
        self.url_fb.setGeometry(QtCore.QRect(120, 60, 81, 16))
        self.url_fb.setTextFormat(QtCore.Qt.RichText)
        self.url_fb.setOpenExternalLinks(True)
        self.url_fb.setObjectName("url_fb")
        
        self.text_fb = QtWidgets.QLabel(self.centralwidget)
        self.text_fb.setGeometry(QtCore.QRect(40, 60, 71, 16))
        self.text_fb.setObjectName("text_fb")
        
        self.descripcion = QtWidgets.QLabel(self.centralwidget)
        self.descripcion.setGeometry(QtCore.QRect(40, 32, 241, 21))
        self.descripcion.setObjectName("descripcion")
        
        self.text_informacion = QtWidgets.QLabel(self.centralwidget)
        self.text_informacion.setGeometry(QtCore.QRect(60, 12, 71, 16))
        self.text_informacion.setObjectName("text_informacion")
        
        self.line_5 = QtWidgets.QFrame(self.centralwidget)
        self.line_5.setGeometry(QtCore.QRect(30, 20, 20, 3))
        self.line_5.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_5.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_5.setObjectName("line_5")
        
        self.line_6 = QtWidgets.QFrame(self.centralwidget)
        self.line_6.setGeometry(QtCore.QRect(140, 20, 330, 3))
        self.line_6.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_6.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_6.setObjectName("line_6")
        
        self.version = QtWidgets.QLabel(self.centralwidget)
        self.version.setGeometry(QtCore.QRect(350, 35, 81, 16))
        self.version.setObjectName("version")
        
        self.win_mode = QtWidgets.QCheckBox(self.centralwidget)
        self.win_mode.setGeometry(QtCore.QRect(330, 60, 111, 20))
        #self.win_mode.setChecked(True)
        self.win_mode.setObjectName("win_mode")
        
        MainWindow.setCentralWidget(self.centralwidget)
        MainWindow.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        
        self.boton_play.clicked.connect(self.launcherExe)
        self.boton_play.clicked.connect(MainWindow.close)
        self.win_mode.clicked.connect(self.estado_caja_verificacio)
        self.main()
    
    def main(self):
        self.ejecutar_barra_carga()
        
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Audition Latino Launcher"))
        self.boton_play.setText(_translate("MainWindow", "Play"))
        self.text.setText(_translate("MainWindow", "Comprobando Archivos..."))
        self.n_archivos.setText(_translate("MainWindow", "0/2058"))
        self.desarrollador.setText(_translate("MainWindow", "Desarrollador: RT"))
        self.url_fb.setText(_translate("MainWindow", "<a href=\"https://www.facebook.com/rhythmtrack\">Rhythm Track</a>"))
        self.text_fb.setText(_translate("MainWindow", "- Facebook:"))
        self.descripcion.setText(_translate("MainWindow", "- Simple launcher para Audition Latino 😊"))
        self.text_informacion.setText(_translate("MainWindow", "Información"))
        self.version.setText(_translate("MainWindow", "Versión: Lite"))
        self.win_mode.setText(_translate("MainWindow", "Modo Ventana"))

        
    def launcherExe(self):
        exe = "Audition.exe"
        key = " /t3enter 15007D45626307077F5C463938635756352D775057"
        subprocess.Popen(exe+key)
        
    def obtener_path(self):
        try:
            path = sys._MEIPASS
            
        except Exception:
            path = os.path.abspath(".")
        
        #print(path)
        return path
    
    def estado_caja_verificacio(self):
        
        estado = self.win_mode.isChecked()
        estado = str(int(estado))
        
        with open("Config.ini","r") as config:
            
            lineas = config.readlines()
               
        for linea in lineas:
            
            if re.findall("WINMODE", linea):
                
                lineas[lineas.index(linea)] = "WINMODE="+estado+"\n"
                
                break
            
        with open("Config.ini","w") as config:
            
            config.writelines(lineas)
                
    def ejecutar_barra_carga(self):
        self.hilo = QtCore.QThread()
        self.trabajo = Area_trabajo()
        self.trabajo.moveToThread(self.hilo)
        
        self.hilo.started.connect(self.trabajo.main)
        self.trabajo.final_trabajo.connect(self.hilo.quit)
        self.trabajo.final_trabajo.connect(self.trabajo.deleteLater)
        self.hilo.finished.connect(self.hilo.deleteLater)
        
        self.trabajo.barra_progreso.connect(self.barra.setValue)
        self.trabajo.enviar_mensaje.connect(self.text.setText)
        self.trabajo.enviar_mensaje_cantidad_archivos.connect(self.n_archivos.setText)
        self.trabajo.modo_ventana.connect(self.win_mode.setChecked)
        self.trabajo.activar_desactivar_modo_ventana.connect(self.win_mode.setEnabled)
        self.trabajo.activar_play.connect(self.boton_play.setEnabled)
        
        self.hilo.start()
        
        
if __name__ == "__main__":
    
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

