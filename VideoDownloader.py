import re
import os
from os.path import isfile, getsize
import urllib
import urllib2
from bs4 import *
"""
A general videodownloader which extracts the video source from any given webpage using regex.
It is still in experimental stage and may or may not work for your source and you are free to make changes to it"""

def request(url):
    req = urllib2.Request(url)
    req.add_header('User-agent', 'Mozilla 5.10')
    return req


def url_extract(url):
    try:
        req = request(url)
        html = urllib2.urlopen(req).read(2000000)
        print "loading ....."
        src = str(html)
        soup = BeautifulSoup(html, "lxml")
        name = str(soup.title.contents[0])[0:250]
        
        #regex to extract https and http urls 
        puller = re.compile(r"http.*?['\";]") 
        
        loop = puller.findall(src)

        sorted = []
        # finding only urls containing video extension
        #TODO find a way to check whether it is a video file or not without all this difficulties
        for x in loop:
            if ('mp4' in x) or ('flv' in x) or (
                    'm3u8' in x) or ('mpg' in x) or ('wmv' in x):
                sorted.append(x)
        realsorted = []

        for x in sorted:
            realsorted.append(x[0:-1])

        ssort = []
        ssort = list(set(realsorted))
        return(ssort, name)
    except Exception as e:
        print '1:', e
        pass


def url_decoder(lists):
    try:
        d = []
        for x in lists:
            x = urllib.unquote(x).decode('utf8')
            d.append(x)
            print x

        for x in d:
            if x[-1] == '/':
                x = x[0:-1]
                d.append(x)
            if x[-3:] == 'amp':
                x = x[0:-3]
                d.append(x)
        return(d)
    except Exception as e:
        print '2:', e
        pass


def videolink_extract(dsort):
    try:
        videolink = []
        ext = []
        size = []
        form = []

        for x in dsort:
            try:
                req = request(x)
                ht = urllib2.urlopen(req)
                meta = ht.info()
                m = meta.getheaders("Content-Type")[0]
                if 'video' in m:
                    videolink.append(x)
                    ext.append(m[-3:])
                    si = int(
                        urllib2.urlopen(req).info().getheaders("Content-Length")[0])
                    size.append(si)
            except:
                pass

        q = re.compile(r"[0-9]{3,4}[Pp]+")
        for x in videolink:
            try:
                f = q.search(x)
                form.append(str(f.group()))
            except:
                form = []
        print form
        return(ext, size, videolink, form)
        # return(ext,size,videolink)
    except Exception as e:
        print '3:', e
        pass


def resume_down(file_name, file_size, url):
    req = request(url)
    cursize = os.path.getsize(file_name)
    req.add_header('Range', 'bytes=%s-%s' % (cursize, file_size))
    r = urllib2.urlopen(req)
    f = open(file_name, 'ab')
    #meta = u.info()
    #file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading : %s \nOrginal MegaBytes: %s" % (file_name, float(file_size) / (1024**2))
    print "Resuming at  : %s" % float(cursize) / (1024**2)
    file_size_dl = cursize
    block_sz = 8192
    while True:
        buffer = r.read(block_sz)
        if not buffer:
            break
        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d [%3.2f%%]" % (
            file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8) * (len(status) + 1)
        print status,
    f.flush()
    f.close()


def dl(file_name, file_size, url):
    try:
        count = 1
        req = request(url)
        u = urllib2.urlopen(req)
        if isfile(file_name):
            if os.path.getsize(file_name) != file_size:
                print "There already exists a file with do you want to resume the download press \'y\' to continue"
                rp = raw_input()
                if rp == 'y':
                    resume_down(file_name, file_size, url)
                    sys.exit()
            else:
                print "%s is already downloaded press \'n\' to stop the download" % file_name
                if raw_input == 'n':
                    sys.exit(0)

            fil = file_name[:-5] + str(count)
            count += 1
            file_name = fil + file_name[-4:]
        f = open(file_name, 'wb')
        #meta = u.info()
        #file_size = int(meta.getheaders("Content-Length")[0])
        print "Downloading: %s \nMegaBytes: %s" % (file_name, float(file_size) / (1024**2))

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break

            file_size_dl += len(buffer)
            f.write(buffer)
            status = r"%10d [%3.2f%%]" % (
                file_size_dl, file_size_dl * 100. / file_size)
            status = status + chr(8) * (len(status) + 1)
            print status,

        f.flush()
        f.close()
    except Exception as e:
        print '4:', e
        pass

if __name__ == "__main__":
    try:
        url = raw_input("Enter url : ")
        print "extracting all the available urls"
        (ss, name) = url_extract(url)
        print "decoding the available urls"
        ds = url_decoder(ss)
        print "extracting videolinks"
        (ext, size, videolink, form) = videolink_extract(ds)
        if (len(form) > 0):
            for i in enumerate(form):
                print i
        else:
            for i in enumerate(size):
                print i
        req = raw_input("press y to continue")
        if req == 'y':
            v = int(raw_input("enter the index of video quality you want"))
            name = name + '.' + ext[v]
            dl(name, size[v], videolink[v])
    except Exception as e:
        print '5:', e
        pass
