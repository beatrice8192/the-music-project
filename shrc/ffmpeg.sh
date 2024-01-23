# https://trac.ffmpeg.org/wiki/AudioVolume

# https://superuser.com/questions/323119/how-can-i-normalize-audio-using-ffmpeg


# ffmpeg -ss 01:43:46 -t 00:00:44.30 -i input.mp3 output.mp3

# ffmpeg -ss 00:00:00 -t 00:02:00 -i 'Abba - Dancing Queen (Official Music Video)-xFrGuyw1V8s.mp3' 'Abba - Dancing Queen (Official Music Video)-120sec-xFrGuyw1V8s.mp3'

# ffmpeg -loop 1 -i '211006 meet after civ.png' -c:v libx264 -t 15 -pix_fmt yuv420p -vf scale=320:240 out.mp4

# ffmpeg -i video.mp4 -i audio.wav -c:v copy -c:a aac output.mp4

# ffmpeg -i video.avi -af "volumedetect" -vn -sn -dn -f null /dev/null

# trim audio to length
# forfile $1 $2 ffmpeg -ss 00:00:00 -t 00:02:00 -i

# forfile $1 $2 ffmpeg -ss 00:00:00 -t 00:02:00 -i INPUT -af \"afade=t=out:st=110:d=10\" OUTPUT

# loudness report per 0.1 second
# ffmpeg -i 'A New Course (Civilization 6 OST)-sR8i2lB_oRg.mp3' -filter_complex ebur128 -f null - 2>&1 | grep -e "Parsed_ebur128" >ebur128.txt

# ffmpeg -nostats -i 'A New Course (Civilization 6 OST)-sR8i2lB_oRg.mp3' -filter_complex ebur128=peak=true -f null - 2>&1 | grep -e "Parsed_ebur128" >ebur128b.txt

# volume transition
# https://stackoverflow.com/questions/38085408/complex-audio-volume-changes-with-ffmpeg

# ffmpeg -i "A New Course (Civilization 6 OST)-sR8i2lB_oRg.mp3" -af "volume=enable='between(t,10,30)':volume='t / 3.0':eval=frame" "A New Course (Civilization 6 OST)-sR8i2lB_oRg v1.mp3"

# ffmpeg -i "A New Course (Civilization 6 OST)-sR8i2lB_oRg.mp3" -af "volume=enable='between(t,10,30)':volume='+10dB':eval=frame" "A New Course (Civilization 6 OST)-sR8i2lB_oRg v2.mp3"

# ffmpeg -i "A New Course (Civilization 6 OST)-sR8i2lB_oRg.mp3" -af "volume=enable='between(t,7,9)':volume='4.79 + (t - 7) / (9 - 7) * (4.41 - 4.79)':eval=frame" "A New Course (Civilization 6 OST)-sR8i2lB_oRg v3.mp3"

# + 10dB = volume * 200%`

function convert_time
{
    seconds=$1
    minutes=$(( $seconds / 60 ))
    hours=$(( $minutes / 60 ))
    seconds=$(( $seconds - $minutes * 60 ))
    minutes=$(( $minutes - $hours * 60 ))
    #seconds=$(echo $(( $seconds + 100 )) | cut -c 2-)
    #minutes=$(echo $(( $minutes + 100 )) | cut -c 2-)
    echo $hours:$minutes:$seconds
}

function ff
{
    option=$1
    input=$2
    case $1 in
        --clip)
            length=$3
            fade=$4
            output=$(echo $input | sed "s|.mp3|_[$length].mp3|g")
            set -x
            if [[ $fade == "" ]]; then
                ffmpeg -ss 00:00:00 -t $(convert_time $length) -i "$input" "$output"
            else
                ffmpeg -ss 00:00:00 -t $(convert_time $length) -i "$input" -af "afade=t=out:st=$(( $length - $fade )):d=$fade" "$output"
            fi
        ;;
        --ebur)
            ffmpeg -i "$input" -filter_complex ebur128=peak=true -f null - 2>&1 | grep -e "Parsed_ebur128" > "$input".ebur
        ;;
        --loudnorm)
            output=$(echo $input | sed "s|.mp3|_[loudnorm].mp3|g")
            set -x
            ffmpeg -i "$input" -filter:a loudnorm "$output"
        ;;
        --normalize)
            output=$(echo $input | sed "s|.mp3|_[ffnorm].mp3|g")
            set -x
            #-b:a 192k
            #-f override output file
            ffmpeg-normalize "$input" -o "$output" -c:a mp3 -f
        ;;
        --pad)
            length=$3
            output=$(echo $input | sed "s|.mp3|_[pad$length].mp3|g")
            set -x
            #,apad=pad_dur=$length
            ffmpeg -i "$input" -af "apad=pad_dur=$length,adelay="$length"s:all=true" "$output"
        ;;
        --silencedetect)
            set -x
            ffmpeg -i "$input" -af "silencedetect=n=-50dB:d=1" -f null -
        ;;
        --volume)
            # +4dB -4dB 0.5 2.0
            volume=$3
            quality=$4
            output=$(echo $input | sed "s|.mp3|_[v$volume].mp3|g")
            if echo $volume | egrep -q "\+|\-"; then
                volume=$volume"dB"
            fi
            if [[ "$quality" != "" ]]; then
                quality="-b:a "$quality"k"
            fi
            set -x
            #-vcodec copy
            ffmpeg -i "$input" -filter:a "volume=$volume" "$output" -c:a mp3 -b:a 192k
        ;;
        --volumedetect)
            set -x
            ffmpeg -i "$input" -af "volumedetect" -vn -sn -dn -f null /dev/null
        ;;
    esac
    set +x
}

# forfile '2020 civ 2.0 industrial' '2020 civ 2.0 industrial norm' ffauto --normalize INPUT OUTPUT

function ffauto
{
    option=$1
    input=$2
    output=$3
    if [[ "$option" == "" ]] || [[ "$input" == "" ]] || [[ "$output" == "" ]]; then
        return
    fi
    case $option in
        --normalize)
            # need to use wav intermediate output to prevent re-sampling
            set -x
            output_ffnorm=$(echo $input | sed "s|.mp3|_[ffnorm].wav|g")
            output_vdetect="$input".out
            ffmpeg-normalize "$input" -o "$output_ffnorm" -f
            ffmpeg -i "$output_ffnorm" -af "volumedetect" -vn -sn -dn -f null /dev/null 2>&1 | tee "$output_vdetect"
            volume=$(cat "$input".out | grep "histogram" | tail -1 | sed "s|.*histogram_||g" | sed "s|db:.*||g")
            output_volume=$(echo $output_ffnorm | sed "s|.wav|_[v$volume].mp3|g")
            ffmpeg -i "$output_ffnorm" -filter:a "volume=+"$volume"dB" "$output" -c:a mp3 -b:a 192k -y
            rm -f "$output_ffnorm" "$output_vdetect"
            set +x
        ;;
        --silencesplit)
        ;;
    esac
}
