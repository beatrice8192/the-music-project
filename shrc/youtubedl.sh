
# youtube-dl
# yt-dlp

alias yy3_128=" alias yy3;      yt-dlp --extract-audio --audio-format mp3"
alias yy3_192=" alias yy3_192;  yt-dlp --extract-audio --audio-format mp3 --audio-quality 192"
alias yy3_best="alias yy3_best; yt-dlp --extract-audio --audio-format best"
alias yy4="     alias yy4;      yt-dlp -f mp4"

function yy3() {
    for file in ${@:1}; do
        yy3_192 "https://www.youtube.com/watch?v=$file"
    done
}

function yy34() {
    yy3 $1
    yy4 $1
}

function yy_read_bookmark() {
    file=$1
    script=$(echo $file | cut -c 1-7)_download_mp3.sh
    # cat $file | egrep "youtube.com.*v=" | sed "s|.*v=||g" | sed "s|[\"\&].*||g" > $script
    cat $file | egrep "youtube.com.*v=" | sed "s|.*v=||g" | sed "s|ICON=\".*\"||g" | sed -E "s|[\"\&](.*)| # \1|g" > $script
    wc -l $file $script
    sed -i "" "s|^|yt-dlp --extract-audio --audio-format mp3 --audio-quality 192|g" $script
    sh $script 2>&1 | tee $script.log
}

function yy_mp3_redo() {
    rm -f _log
    for file in ${@:1}; do
        hash=$(echo $file | sed "s|.*\[||g" | sed "s|\].*||g")
        mv "$file" "$file.old"
        yy3_192 "https://www.youtube.com/watch?v=$hash" | tee -a _log
    done
}

