#for file in *.tar.gz; mkdir $file; do tar -zxf $file -C $file; done

%%bash

n=$(find ./ -maxdepth 3 -name '*tar.gz' | wc -l)
i=1

for archive in $(find ./ -maxdepth 3 -name '*tar.gz'); do
    echo "<----- $i / $n: $(basename $archive)"
        
    
    
    # Create directory for storage
    s=$archive
    s=${s##*/}
    s=${s%.*}
    s=${s%.*}
    mkdir $s
    
    # Extract archive
    tar -xzvf $archive -C $s/
    
    
    # Iterate count
    let i+=1
done

echo "Done!"