# -*- coding: utf-8 -*-
import numpy as np
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QWidget, QListWidget, QListWidgetItem, QLabel, QPushButton, QGridLayout, QApplication
import urllib.request, json
import datetime as dt
import pylab as plb
import matplotlib.pyplot as plt # font,wykres
import matplotlib.patheffects as PathEffects

#pobranie pliku json i otworzenie go
file = urllib.request.urlopen('http://api.nbp.pl/api/exchangerates/tables/a/last/10?format=json').read().decode('utf8')
values = json.loads(file)
# do obliczen wybrałem 10 ostatnich kursów
#czcionka dla wykresu
plt.rc('font', family='serif', serif='Times New Roman')
#interpolacja-przyjmowanie w pewnym przedziale funkcji znanych wartosci dla danych liczb
#interpolacja wielomianowa metodą Lagrange-a, punkty interpolacji są tam gdzie zielona linia przecina niebieska
#interpolacja wielomianowa metodą Lagrange-a ma na celu przyblizenia danych, Lagrange udowodnił, że wielomian odpowiednio wysokiego stopnia może interpowolować każdy zbiór danych, ale nie zawsze można dobrać taki wielomian 
def interpolacja_lagrange(x, y, xval):
    """
    x - argument funkcji
    y - wartość funkcji
    xval - wartość interpolowana funkcji
    funkcja obliczajaca wartosc interpolowana funkcji yval w punkcie xval
    """
    products = 0
    yval = 0
    for i in range(len(x)):
        products = y[i]
        for j in range(len(x)):
            if i != j:
                products = products * (xval - x[j]) / (x[i] - x[j])
        yval = yval + products
    return yval
#aproksymacja ma za zadanie przyblizenie konkretną funkcje danego zbioru danych
#aproksymacja(ocena na oko,dopasowanie jak z najmniejszym bledem) i wykres
def swapRows(v,i,j):
    if len(v.shape) == 1:
        v[i],v[j] = v[j],v[i]
    else:
        v[[i,j],:] = v[[j,i],:]
     
def swapCols(v,i,j):
    v[:,[i,j]] = v[:,[j,i]]

    
#elimacja gaussa->tabela przestawna ,algorytm macierzowy,musielismy przerzucic macierz
def elimacjagaussa(a, b, tol = 1.0e5):
    n = len(b)
    s = np.zeros(n)  
    for i in range(n):
        s[i] = max(np.abs(a[i,:]))
    
    for k in range(0, n-1):
        p = np.argmax(np.abs(a[k:n, k])/s[k:n])+k
        if abs(a[p, k])<tol:
            
            pass#wypełniacz,nic nie robi
        if p != k:
            swapRows(b, k, p)
            swapRows(s, k, p)
            swapRows(a, k, p)
        
        for i in range(k+1, n):
            if a[i, k] != 0.0:
                lam = a[i, k]/a[k, k]
                a[i, k+1:n] = a[i, k+1:n]-lam*a[k, k+1:n]
                b[i] = b[i]-lam*b[k]
        
    if abs(a[n-1, n-1])<tol:
       
        pass
    
    b[n-1] = b[n-1]/a[n-1, n-1]
    for k in range(n-2, -1, -1):
        b[k] = (b[k]-np.dot(a[k, k+1:n], b[k+1:n]))/a[k, k]
    
    return b
    
    
#Można zastosować funkcję numpy.polyfit() do
#doboru współczynników wielomianu
def polyFit(xData, yData, m): #zwraca współczynniki dla wielomianu stopnia, który jest najlepiej dopasowany//(xData, yData,m)(zbior aproksymowany,stopien wielomianu
    a = np.zeros((m+1, m+1))#macierz A
    b = np.zeros(m+1)#macierz B
    s = np.zeros(2*m+1)#w wektorze s składowane są obliczeni pośrednie, które kopiowane są dalej do macierzy a

#b=
    for i in range(len(xData)):
        temp = yData[i]
        for j in range(m+1):
            b[j] = b[j]+temp
            temp = temp*xData[i]
#a=            
        temp = 1.0
        for j in range(2*m+1):
            s[j] = s[j]+temp
            temp = temp*xData[i]
    
    for i in range(m+1):
        for j in range(m+1):
            a[i, j] = s[i+j]
    
    return elimacjagaussa(a, b)

    
#coeff-coefficients-współczynniki
def plotPoly(title, xData, yData, coeff, xlab = 'DNI', ylab = 'KURS WARTOŚCI PLN'):
    m = len(coeff)
    x1 = min(xData)
    x2 = max(xData)
    dx = (x2-x1)/10.0 #wyliczenie kroku daty, szczegolowosc wykresu
    x = np.arange(x1, x2+dx/10.0, dx)
    y = np.zeros((len(x)))*3.0
    for i in range(m): #obliczanie wielomianu
        y = y+coeff[i]*x**i
    plt.figure('Wykres')
    plt.clf()
    plt.plot(xData, yData, '.-', label ='Wartości dokładne')
    plt.plot(x, y, '-g', label ='Wartości aproksymowane')
    plt.legend()
    plt.legend(loc='lower center',bbox_to_anchor=(0.07, 0.03),fancybox=True, shadow=True)#legenda
    #plt.legend(loc='lower center',bbox_to_anchor=(0.5, 1.15),fancybox=True, shadow=True)#legenda
    plt.xlabel(xlab); plt.ylabel(ylab)
    plt.grid(True)
    plt.title(title)
    plt.show()



opis = """
Wartosci z # oznaczaja braku 
pomiaru w danym dniu. W zamian została
obliczona ich interpolacja.
"""+10*'\n'


 
class Program(QWidget): #Klasa 'Program' dziedziczy po Qwidget
  
    def __init__(self):#Konstruktor – tu zaczyna się wykonywanie kodu programu;'self'odnosi się do obiektu klasy 'Program'
        super().__init__()

         
        self.wybierz_walute = QLabel('Wybierz walutę:'+30*' ') #'+*' szerokosc pola wyboru waluty
        self.wybierz_walute.setStyleSheet("QLabel {background-color: grey; color : none}")
        self.informacja = QLabel('Informacja:'+1*' ')
        self.informacja.setStyleSheet("QLabel {background-color: grey; color : none}")
        self.opis = QLabel(opis)
        self.opis.setStyleSheet("QLabel {background-color: none; color: none")
        self.bwybierz = QPushButton('Wybierz')
        self.bwyjscie = QPushButton('Wyjście')
        self.list = QListWidget()
        for i in range(len(values[0]['rates'])):
            item = QListWidgetItem('%s (%s)' % (values[0]['rates'][i]['code'], values[0]['rates'][i]['currency']))
            self.list.addItem(item)
         
        #siatka
        siatka = QGridLayout()
        siatka.setSpacing(1)

        siatka.addWidget(self.wybierz_walute, 0, 1)#(y,x)
        siatka.addWidget(self.list, 1,1 )
        
        siatka.addWidget(self.bwybierz, 2, 1)
        siatka.addWidget(self.bwyjscie, 2,0)
        
        siatka.addWidget(self.informacja, 0,0)
        siatka.addWidget(self.opis, 1, 0)
        
        
        self.setLayout(siatka)#włącz siatkę

        #łączy zdarzenie przycisku z funkcją wybranie()
        #pobiera indeks waluty
        self.bwybierz.clicked.connect(self.wybranie)
        

        #zdarzenie przycisku wyjscie
        self.bwyjscie.clicked.connect(self.wyjscie)
        
        self.setGeometry(300, 300, 300, 320)# (self, int ax, int ay, int aw, int ah)
        self.setWindowTitle('Kurs walut')
        self.show()

        #przypisywanie tla
        oImage = QImage("projekt mn.png")
        self.setWindowIcon(QIcon('ikonka.png'))
        szerokosc = 100
        wysokosc = 100
        sImage = oImage.scaled(QSize(szerokosc, wysokosc))
        palette = QPalette()
        palette.setBrush(10, QBrush(sImage))
        self.setPalette(palette)
        

    def wybranie(self):
        sender = self.sender() #kto wykonal polecenie
        a = self.list.currentRow()
        print('Wybrana waluta: %s' % values[0]['rates'][a]['code'])

        temp = []
        yappr = []
        #przypisywanie tla
        oImage = QImage("tlo2.png") 
        szerokosc = 100
        wysokosc = 100
        sImage = oImage.scaled(QSize(szerokosc, wysokosc))
        palette = QPalette()
        palette.setBrush(10, QBrush(sImage))
        self.setPalette(palette)
        for i in range(len(values)):
            relatywnosc_dni = (dt.datetime.strptime(values[i]['effectiveDate'], '%Y-%m-%d') - dt.datetime.strptime(values[i-1]['effectiveDate'], '%Y-%m-%d')).days
            if relatywnosc_dni>1:
                j=0
                y = [values[i-1]['rates'][a]['mid'], values[i]['rates'][a]['mid']]
                x = [i for i in range(len(y))]
                xval = [i for i in np.arange(0, 1, 1/relatywnosc_dni)]
                yval = []
                ytemp = []
                print('Interpolacja w dniach: %s - %s:' % (values[i-1]['effectiveDate'], values[i]['effectiveDate']))
                for xv in xval:
                    data = (dt.datetime.strptime(values[i]['effectiveDate'], '%Y-%m-%d')-dt.timedelta(days=relatywnosc_dni-j)).__format__('%Y-%m-%d')
                    yval.append ('%s:#    %.4f\n' % (data, interpolacja_lagrange(x, y, xv)))
                    ytemp.append(interpolacja_lagrange(x, y, xv))
                    j+=1                   
                for j in range(1, len(yval)):
                    temp.append(yval[j])
                    yappr.append(ytemp[j])
                temp.append ('%s: %.2f\n' % (values[i]['effectiveDate'], values[i]['rates'][a]['mid']))
                yappr.append (values[i]['rates'][a]['mid'])
            else:
                yappr.append (values[i]['rates'][a]['mid'])
                temp.append ('%s: %.2f\n' % (values[i]['effectiveDate'], values[i]['rates'][a]['mid']))
        print(30*'**')
        temp.reverse()
        text = ''.join(temp)
        self.opis.setText(text)
        self.informacja.setText('Kursy wybranej waluty: ')
        xappr = [i for i in range(0, len(yappr))]
        coeff = polyFit(xappr, yappr, 6)
        plotPoly('Kurs '+values[0]['rates'][a]['code'], xappr, yappr, coeff)

        
             

        
    def wyjscie(self):
         app = QApplication(sys.argv)
         sys.exit(app.exec_())
                   

        

if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = Program()
    font=app.font()
    font.setPointSize(12)
    font.setBold(True)
    app.setFont(font)
    sys.exit(app.exec_())
"""
Program główny:
uruchom pętlę
'app', uruchom
okno 'ex' 
"""
