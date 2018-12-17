import libvirt
import uuid
from shutil import copy2
import random
from xml.dom import minidom

from flask import Flask, render_template, redirect, jsonify
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap
from wtforms import StringField, IntegerField, SelectField
from wtforms.validators import InputRequired, IPAddress


app = Flask(__name__)
Bootstrap(app)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

conn = libvirt.open("")
names = conn.listAllDomains()


def createDomain(name,memoria,cpu,ip):

    UUID = str(uuid.uuid4())
    new_dom_xml = open('domain.xml')
    xml = new_dom_xml.read()
    mac = str(generateUniqueMac())
    for domain in names:
        if domain.info()[0] == 1:
            domain.destroy()
    xml = xml.replace('#{NOME}', name)
    xml = xml.replace('#{UUID}', UUID)
    xml = xml.replace('#{MEMORIA}', str(memoria))
    xml = xml.replace('#{CPU}', str(cpu))
    xml = xml.replace('#{DISK}', cloneDisk(name))
    xml = xml.replace('#{MAC}', mac)

    setIP(mac, ip)

    print(xml)

    dom_ref = conn.defineXML(xml)

    dom_ref.create()




def setIP(mac, ip):
    template_ip = f'<host mac="{mac}" ip="{ip}"/>'
    network = conn.networkLookupByName("default")
    result = network.update(libvirt.VIR_NETWORK_UPDATE_COMMAND_ADD_FIRST, libvirt.VIR_NETWORK_SECTION_IP_DHCP_HOST, -1, template_ip)

def cloneDisk(name):
    diskname = name+'.qcow2'
    diskPath = '/home/joao/PycharmProjects/2VaAssad/imagem.qcow2'
    diskCopyPath = '/home/joao/PycharmProjects/2VaAssad/%s' % name
    copy2(diskPath, diskCopyPath)
    return diskCopyPath

def randomMAC():
     mac = [0x00, 0x16, 0x3e,
        random.randint(0x00, 0x7f),
        random.randint(0x00, 0xff),
        random.randint(0x00, 0xff)]
     mac = ":".join(map(lambda x: "%02x" % x, mac))
     return mac


def getMacByDomain(domain):
    domain = conn.lookupByName(domain)
    data = domain.XMLDesc()
    xml = minidom.parseString(data)
    node = xml.getElementsByTagName('mac')
    mac = node[0].attributes['address'].value
    return mac


def generateUniqueMac():
    domains = conn.listDefinedDomains()
    mac = randomMAC()
    macs = map(getMacByDomain, domains)
    if mac in macs:
        mac = randomMAC()
    return mac

def getMemoryNumber(numero,base):

    if base == "KB":
        return numero
    elif base == "MB":
        return numero*1024
    elif base == "GB":
        return (numero*1024)*1024

class VirtForm(FlaskForm):
    hostname = StringField('Hostname:', validators=[InputRequired()])
    memory = IntegerField('Memory:', validators=[InputRequired()])
    cpu = IntegerField("CPU:", validators=[InputRequired()])
    unity = SelectField("Unity:",choices=[('KB', 'KB'), ('MB', 'MB'), ('GB', 'GB')], validators=[InputRequired()])
    ip = StringField('IPv4:', validators=[InputRequired(), IPAddress(ipv4=True, ipv6=False)])

@app.route('/form', methods=['GET', 'POST'])
def form():
    form = VirtForm()
    if form.validate_on_submit():
        nome = form.hostname.data
        memoria = int(form.memory.data)
        base = form.unity.data
        cpu = int(form.cpu.data)
        ip = form.ip.data

        memoria = getMemoryNumber(memoria, base)

        createDomain(nome, memoria, cpu,ip)

        jsonResultado = {}

        jsonResultado['name'] = nome
        jsonResultado['memoria'] = memoria
        jsonResultado['cpu'] = cpu
        jsonResultado['ip'] = ip

        return jsonify(jsonResultado)

    return render_template('home.html', form=form)

@app.route('/')
def root():
    return redirect("/form", code=302)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')