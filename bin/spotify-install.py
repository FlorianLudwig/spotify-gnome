import os
import urllib
from sgmllib import SGMLParser
import subprocess as sp
import platform
import shutil

POOL = 'http://repository.spotify.com/pool/non-free/s/spotify/'
BASE = ''
SPOTIFY_SHARE = os.path.expanduser('~/.cache/spotify-install/')
DEB_CACHE = os.path.expanduser('~/.cache/spotify-deb-cache/')

SYSTEM = 'amd64' # uname -p'


class URLLister(SGMLParser):
    """parse all href="" deb urls from a page"""
    def reset(self):
        SGMLParser.reset(self)
        self.urls = []

    def start_a(self, attrs):
        href = [v for k, v in attrs if k=='href' and v.endswith('.deb')]
        if href:
            self.urls.extend(href)


def check_for_updates():
    arch = '_amd64' if platform.machine() == 'x86_64' else '_i386'
    # make sure needed directories exist
    if not os.path.exists('cache'):
        os.mkdir('cache')

    usock = urllib.urlopen(POOL)
    parser = URLLister()
    parser.feed(usock.read())
    usock.close()
    parser.close()

    # make sure all needed .debs are downloaded
    main_client = None
    if not os.path.exists(DEB_CACHE):
        os.makedirs(DEB_CACHE)

    for url in parser.urls:
        if url.startswith('spotify-client_') and arch in url:
                    main_client = url
        if not os.path.exists(DEB_CACHE + url):
            if '_all' in url or arch in url:
                print url, 'downloading ...'
                open(DEB_CACHE + url, 'w').write(urllib.urlopen(POOL + url).read())
            else:
                print url, 'wrong arch'
        else:
            print url, 'cached'

    if not main_client:
        print 'Could not find main deb file'
        return

    if not os.path.exists(SPOTIFY_SHARE + 'source:' + main_client):
        print 'update available'

        print DEB_CACHE + '/' + main_client
        proc = sp.Popen(['ar', 'x', main_client], cwd=DEB_CACHE)
        if not os.path.exists(DEB_CACHE + 'tmp'):
            os.makedirs(DEB_CACHE + 'tmp')
        assert proc.wait() == 0
        proc = sp.Popen(['tar', '-zxf', '../data.tar.gz'], cwd=DEB_CACHE+'tmp')
        proc.wait()


        #
        if os.path.exists(SPOTIFY_SHARE):
            shutil.rmtree(SPOTIFY_SHARE)

        os.makedirs(SPOTIFY_SHARE)

        src = DEB_CACHE+'tmp/usr/share/spotify/'
        for fname in os.listdir(src):
            shutil.move(src + fname, SPOTIFY_SHARE)

        # create symbolic links for
        lib = '/usr/lib64/' if platform.machine() == 'x86_64' else '/usr/lib/'
        proc = sp.Popen(['ldd', SPOTIFY_SHARE + 'spotify'],
                        stderr=open('/dev/null', 'w'), stdout=sp.PIPE)
        stdout = proc.stdout.read()
        proc.wait()
        for line in stdout.split('\n'):
            line = line.split('=>')
            if len(line) > 1 and 'not found' in line[1]:
                libname = line[0].strip()
                base = libname[:libname.rfind('.so')+3]
                name = base.split('/')[-1]
                if os.path.exists(lib + base):
                    os.symlink(lib + base, SPOTIFY_SHARE + libname)
                else:
                    print 'ERROR', base

        open(SPOTIFY_SHARE + 'source:' + main_client, 'w')


if __name__ == '__main__':
    check_for_updates()


# convert using alien
#os.chdir('alien')
#for url in parser.urls:
#    if not url.endswith('i386.deb'):
#        print url, 'converting with alien'
#        os.system('./alien.pl --to-rpm ../cache/' + url)


#'ldd /usr/bin/spotify  > /dev/null'
# ln -s /usr/lib64/libssl.so ~/.cache/spotify-install/libssl.so.0.9.8

	#libnss3.so.1d => not found
	#libnssutil3.so.1d => not found
	#libsmime3.so.1d => not found
	#libplc4.so.0d => not found
	#libnspr4.so.0d => not found