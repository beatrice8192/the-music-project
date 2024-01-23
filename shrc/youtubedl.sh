
# youtube-dl
# yt-dlp

alias yt3="     alias yt3;      yt-dlp --extract-audio --audio-format mp3"
alias yt3_192=" alias yt3_192;  yt-dlp --extract-audio --audio-format mp3 --audio-quality 192"
alias yt3_best="alias yt3_best; yt-dlp --extract-audio --audio-format best"
alias yt4="     alias yt4;      yt-dlp -f mp4"

function yt34 {
    yt3 $1
    yt4 $1
}

function yt_read_bookmark() {
    file=$1
    script=$(echo $file | cut -c 1-7)_download_mp3.sh
    # cat $file | egrep "youtube.com.*v=" | sed "s|.*v=||g" | sed "s|[\"\&].*||g" > $script
    cat $file | egrep "youtube.com.*v=" | sed "s|.*v=||g" | sed "s|ICON=\".*\"||g" | sed -E "s|[\"\&](.*)| # \1|g" > $script
    wc -l $file $script
    sed -i "" "s|^|yt-dlp --extract-audio --audio-format mp3 |g" $script
    sh $script 2>&1 | tee $script.log
}

