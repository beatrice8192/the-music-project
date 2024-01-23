
list=$1

function file_norm
{
    file=$1
    newfile=$(echo $file | sed "s| |_|g" | tr -d '(){},?!:;"' | tr -d "'")
    mv "$file" "$newfile"
    echo "$newfile"
}
function calculate_amplify
{
    mean_volume=$(echo $1 | cut -d '.' -f 1)
    amplify=0
    if [ $mean_volume -gt -15 ]; then
        amplify=$(( (-15) - $mean_volume ))
    fi
    echo $amplify
}
#for file in *; do
#    file_norm $file
#done

mkdir cmd
if [[ "$list" == "" ]]; then
    list=$(ls *.mp3)
fi
for file in $list; do
    if [[ $file =~ norm ]]; then
        continue
    fi
    input=$file
    output=$(echo $input | sed "s|.mp3|_[norm].mp3|g")
    ffmpeg -i "$input" -filter_complex ebur128=peak=true -f null - 2>&1 | grep -e "Parsed_ebur128" > "$input".ebur
    ffmpeg -i "$input" -af "volumedetect" -vn -sn -dn -f null /dev/null > "$input".vdetect 2>&1
    mean_volume=$(grep mean_volume "$input".vdetect | rev | cut -d ' ' -f 2 | rev)
    amplify_volume=$(calculate_amplify $mean_volume)

    rm -f "$input".cmd "$output"
    touch "$input".cmd
    printf "# shifting $amplify_volume\n" >> "$input".cmd
    printf "ffmpeg -i \"$input\" -af \"\\" >> "$input".cmd
    python3 norm.py -i "$input".ebur -a "$amplify_volume" >> "$input".cmd
    printf "\" \"$output\"" >> "$input".cmd
    sh "$input".cmd
    rm -f "$input" "$input".ebur #"$input".cmd
    mv *.cmd *.vdetect cmd
    mv "$output" "$input"
done
