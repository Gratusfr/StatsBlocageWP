import pywikibot
import datetime
import json
site = pywikibot.Site('fr', 'wikipedia')
#variables

#marge de 10min pour éviter de compter les blocages précipités si en première position
ME = datetime.timedelta(seconds=600) 
ME_flag = False

c=0 #compteur
blocage_total = datetime.timedelta() #duree du blocage total
blocage_indef_actuel = '' #bool le compte fait actuellement l'objet d'un blocage indef
nb_blocage = 0 #compte le nombre de blocages (block)
last_unblock = False #le log d'avant est un déblocage
last_indef = True #le log d'avant est un indef
last_unblock_timestamp = datetime.time() #mémorise le timestamp du déblocage précédent
last_reblock_expiry = '' #mémorise le expiry du reblocage précédent
last_reblock = '' #reblock
last_indef_timestamps = datetime.time() #timestamp dernier blocage indef
t_block = datetime.time() #variable temporaire pour retenir le timestamp du dernier blocage

#date du dernier blocage : timestamp du blocage indef ou expiry du blocage classique
final_time = datetime.time()
#date du premier blocage
first_time = datetime.time() 

#remet les valeurs à zero
def reset_variables():
    global c
    c = 0
    global blocage_total 
    blocage_total = datetime.timedelta()
    global nb_blocage 
    nb_blocage = 0
    global last_unblock
    last_unblock = False
    global last_unblock_timestamp
    last_unblock_timestamp = datetime.time()
    global blocage_indef_actuel 
    blocage_indef_actuel= ''
    global final_time
    final_time = datetime.time()
    global first_time
    first_time = datetime.time()
    global last_indef_timestamps
    last_indef_timestamps = datetime.time()
    global last_indef
    last_indef = True
    global ME_flag 
    ME_flag = False
    global t_block
    t_block = datetime.time()
    global last_reblock_expiry
    last_reblock_expiry = ''
    global last_reblock
    last_reblock = ''

#donne la date du dernier blocage indef
def set_final_time(l):
    global final_time
    global last_indef
    global last_indef_timestamps
    global c
    
    if(blocage_indef_actuel == True and last_indef == True):
        if(is_indef(l)):
            last_indef_timestamps = l.timestamp()
        else:
            last_indef = False
            
    if(blocage_indef_actuel == False and c<2):
        last_indef_timestamps = None
        

#s'il dispose d'une date d'expiration
def is_with_expiry(l):
    if(l.expiry() is None):
        return True
    else:
        return False

#s'il s'agit d'un blocage indef
def is_indef(l):
    if(l.expiry() is None and (l.action() == "block" or l.action() == "reblock")):
        return True
    else:
        return False

#s'il s'agit d'un déblocage
def is_unblock(l):
    if(l.action() == "unblock"):
        return True
    else:
        return False

#s'il s'agit d'un reblock
def is_reblock(l):
    if(l.action() == "reblock"):
        return True
    else:
        return False
    
#incrémente la durée du blocage
def add_blocage_total(l):
    global blocage_total
    global last_unblock
    global last_unblock_timestamp
    global ME
    global ME_flag
    global first_time
    global t_block
    global last_reblock_expiry
    global last_reblock
    
    ME_flag = False
    
    #gère les cas de déblocages
    if(last_unblock):
        if(last_unblock_timestamp - l.timestamp() < ME ):
            ME_flag = True
            first_time = l.timestamp()
        blocage_total += last_unblock_timestamp - l.timestamp()
    else:
        #si le dernier n'est pas un déblocage
        if(not ME_flag and l.action() == "block"):
            t_block = l.timestamp()
        if (not is_with_expiry(l)):
            #si fini
            if(is_reblock(l)):
                #si reblocage
                if(last_reblock_expiry == ''):
                    last_reblock_expiry = l.expiry()
                else:
                    if(last_reblock_expiry < l.expiry()):
                        last_reblock_expiry = l.expiry()
            else:
                if(last_reblock):
                    #print('---', last_reblock_expiry, l.timestamp())
                    if(not last_reblock_expiry == ''):
                        blocage_total += last_reblock_expiry - l.timestamp()
                    else:
                        blocage_total += l.duration()
                else:
                    blocage_total += l.duration()

    #met à jour l'état de déblocage
    if(is_unblock(l)):
        last_unblock = True
        last_unblock_timestamp = l.timestamp()
    else:
        last_unblock = False
    
    if(is_reblock(l)):
        last_reblock = True
    else:
        last_reblock = False
        last_reblock_expiry = ''

#calcul amplitude
def amplitude(first_time, last_indef_timestamps, secondes):
    if(last_indef_timestamps == '' or last_indef_timestamps == None):
        d = 'None'
    else:
        if(secondes):
            d = last_indef_timestamps - first_time
            d = d.total_seconds()
        else:
            d = str(last_indef_timestamps - first_time)
    return d
#affiche les résultats dans un fichier Json
def display_results(user):
    data = {}
    data['user'] = str(user)
    data['blocage_total'] = str(blocage_total)
    data['blocage_total_seconds'] = blocage_total.total_seconds()
    data['blocage_indef_actuel'] = blocage_indef_actuel
    data['nb_blocage'] = nb_blocage
    data['first_time'] = str(first_time)
    data['last_indef_timestamps'] = str(last_indef_timestamps)
    data['amplitude'] = amplitude(first_time, last_indef_timestamps, False)
    data['amplitude_seconde'] = amplitude(first_time, last_indef_timestamps, True)
    print(json.dumps(data))

#main
def get_log_user(name):
    global blocage_indef_actuel
    global c
    global nb_blocage
    global first_time
    
    #récupération du log
    cible = pywikibot.User(title=name, source=site)
    logs = site.logevents(page=cible, logtype="block")
    
    #lecture du log
    for l in logs :
        #print(l.page(), l.action(), l.timestamp(),l.user(),l.duration(),l.expiry())
        
        #regarde si le log le plus récent est un blocage indef
        if(blocage_indef_actuel == ''):
            blocage_indef_actuel = is_indef(l)
            
        #Dernier blocage indef
        set_final_time(l)

        #incrémente les blocages
        if(l.action() == "block"):
            nb_blocage += 1

        #incrémentation de la durée du blocage
        add_blocage_total(l)
        #incrémentation du compteur
        c=c+1
    
    #levée d'une exception si user sans blocage ou inexistant
    if (c==0):
        reset_variables()
        raise Exception('L\'utilisateur ', user , ' n\'a jamais été bloqué ou n\'existe pas.')
        
    if(ME_flag):
        first_time = t_block
    else:
        first_time = l.timestamp()
    
    #affichage des résulats
    display_results(user)
    #remise à zero des variables
    reset_variables()

#utilisateurs à analyser
users = [] # liste des bannis de [[categorie:Utilisateur banni]]

for user in users :
    try:
        get_log_user(user)
    except Exception as e:
        print(e)