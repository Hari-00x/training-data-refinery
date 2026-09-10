from warcio.archiveiterator import ArchiveIterator

with open("CC-MAIN-20241101184224-20241101214224-00000.warc.wet.gz",'rb') as stream:

    count=0

    for record in ArchiveIterator(stream):

        if record.rec_type=='conversion':

            url=record.rec_headers.get_header("WARC-Target-URI")

            content=record.content_stream().read().decode("utf-8",errors="ignore")

            print(f"---Record{count}---")

            print(f"URL: {url}")

            print(f"Text length: {len(content)} chars")

            print(f"Preview: {content[:300]}")

            print()

            count+=1

            if count>=5:

                break

