#####IMPORT######
from shelper import SocketHelper
import json
import collections
import virtualbox #pyvbox

vbox = virtualbox.VirtualBox()


#####FONCTIONS######

#Renvoie la liste des vm d'un utilisateur au format json :
#"{"listing_vm": "iduser", "vm_x":  "nomvm" ...}" si la fonction trouve quelque chose
#"{"listing_vm": "iduser"}" si la fonction ne trouve aucune vm

def listingvm(id):
    vmlisting = collections.OrderedDict()  # Dictionnaire ordonne
    vmlisting['listing_vm'] = iduser #Premier element du dictionnaire
    vmnb = 0  # nombre de vm avec l'id
    for vm in vbox.machines: # Pour chaque vm
        vmname = vm.name
        i = 0
        if '_' in vmname: #Si le caractere _ est present dans le nom de la vm
            while vmname[i] != "_":  # Tant que le caractere a la position "i" n'est pas _ alors
                i += 1  # Incremente de 1 le compteur
        if iduser == vmname[:i]:  # Si on trouve une vm avec l'id
            vmnb += 1  # Incremente de 1 le nb de vm avec l'id
            vmlisting['vm_' + str(vmnb)] = vmname
    return vmlisting #Envoi des informations

#Renvoie la liste des vm et de leurs etats (en ligne, hors ligne)
#"{"state_vm": "1", "nomvm: "etat", ...}" Si la fonction trouve une vm et son etat (on/off)
#"{"state_vm": "1213"}" Sinon si la fonction ne trouve rien

def statevm(id):
    list1 = listingvm(id) #json
    vmstate = collections.OrderedDict()
    vmstate['state_vm'] = iduser
    for key, value in list1.iteritems():
        if 'vm_' in key: #S'il y a des vm
            vmfind = vbox.find_machine(value) #recupere les infos de la vm
            etat = vmfind.state #Recupere l'etat de la vm
            if str(etat) == "FirstOnline": #Si la vm est en ligne
                etat = "on"
                vmstate[value] = etat
            elif str(etat) == 'PoweredOff': #Si la vm est hors ligne
                etat = "off"
                vmstate[value] = etat
    return vmstate

#Creation du json et encodage en utf-8
def jsondata(raw):
    jdata = json.dumps(raw)
    jdata = jdata.decode('unicode-escape').encode('utf-8')  # Decode lunicode et rencode en utf8, a desactiver si le php ne le supporte pas
    return jdata

#Conversion bytes/Mo en octets et equivalent
def convert(size, type):
    suffixes = 0
    if type == 'bytes':
        suffixes = ["octets", "Ko", "Mo", "Go", "To"]
    elif type == 'Mo':
        suffixes = ["Mo", "Go", "To"]
    tmpSize = size
    i = 0
    while (tmpSize >= 1024):
        tmpSize /= 1024.0
        i+=1
    tmpSize *= 100
    tmpSize = int(tmpSize + 0.5)
    tmpSize /= 100
    return tmpSize, suffixes[i]

#Renvoie la liste des vm et de leurs caracteristiques (nom,description,os,cpu,ram,stockage logique, stockage reel)
#"{"infos_vm": "123", "vm_1": {"nom": "x", "desc": "x", "os": "x", "cpu": x, "ram": [x, "unit"], "sto_l": [x, "unit"], "sto_r": [x, "unit]}, "vm_2": { ... }}
#"{"state_vm": "123"}" Sinon si la fonction ne trouve rien

def infosvm(id):
    vmlisting = listingvm(id)
    vminfos = collections.OrderedDict()
    vminfos['infos_vm'] = iduser
    vmnb = 0  # nombre de vm avec l'id
    for key, value in vmlisting.iteritems():
        if 'vm_' in key: #S'il y a des vm
            vmnb +=1
            vm = collections.OrderedDict() #Creation d'un dictionnaire ordonnee pour cette vm
            vmfind = vbox.find_machine(value)  #Recupere les infos de la vm
            vm['nom'] = vmfind.name
            vm['desc'] = vmfind.description
            vm['os'] = vmfind.os_type_id
            vm['cpu'] = vmfind.cpu_count
            ramsize = vmfind.memory_size
            print ramsize
            vm['ram'] = convert(ramsize,'Mo') #Conversion Mo en Go/To
            mediums = vmfind.medium_attachments
            sizehddlog = 0 #Taille du stockage logique sur la vm
            sizehddreal = 0 #Taille reel du stockage de la vm
            for med in mediums:
                type = med.type_p #Recupere le type du medium (hdd, cd ...)
                type = str(type) #Conversion en string
                if type == 'HardDisk':
                    sizehddlog = med.medium.logical_size + sizehddlog  # Totalite du stockage logique sur la vm, meme si plusieurs hdd
                    sizehddreal = med.medium.size + sizehddreal
            vm['sto_l'] = convert(sizehddlog,'bytes')
            vm['sto_r'] = convert(sizehddreal, 'bytes')
            vminfos['vm_' + str(vmnb)] = vm #On ajoute les infos de la vm numero x dans le dictionnaire correspondant
    return vminfos #Envoi des informations


#####PROGRAMME PRINCIPAL######

#Creation de la socket reseau
sockethelper = SocketHelper("192.168.1.11",1333)

#Tant que toujours vrai (afin d'etre toujours actif)
while True:

    sockethelper.s_accept() #On accepte toutes les connexions

    data = sockethelper.read_data() #On lis le flux entrant

    python_obj = json.loads(data) #Chargement du json recu

    #Listing des vms pour un utilisateur
    if 'listing_vm' in data:

        iduser = python_obj['listing_vm']
        lvm = listingvm(iduser) #Appel de la fonction listingvm
        lvm = jsondata(lvm) #Appel de la fonction jsondata
        sockethelper.send_data(lvm) #Envoi des informations en json
        sockethelper.close_socket() #Fermeture de la socket

    elif 'state_vm' in data:

        iduser = python_obj['state_vm']
        svm = statevm(iduser)
        svm = jsondata(svm) #Appel de la fonction jsondata
        sockethelper.send_data(svm) #Envoi des informations en json
        sockethelper.close_socket() #Fermeture de la socket

    elif 'infos_vm' in data:

        iduser = python_obj['infos_vm']
        ivm = infosvm(iduser)
        ivm = jsondata(ivm)
        sockethelper.send_data(ivm) #Envoi des informations en json
        sockethelper.close_socket() #Fermeture de la socket

    else:
        sockethelper.send_data("Erreur")
        sockethelper.close_socket()