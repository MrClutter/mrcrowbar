from mrcrowbar import models as mrc
from mrcrowbar import utils

from array import array

import pyaudio

SAMPLE_WIDTH_UINT8 = (pyaudio.paUInt8, b'\x80')
SAMPLE_WIDTH_INT8 = (pyaudio.paInt8, b'\x00')
SAMPLE_WIDTH_INT16_LE = (pyaudio.paInt16, b'\x00\x00')
#SAMPLE_WIDTH_INT24_LE = (pyaudio.paInt24, b'\x00\x00\x00')
SAMPLE_WIDTH_INT32_LE = (pyaudio.paInt32, b'\x00\x00\x00\x00')

#: Perform no audio interpolation and let PortAudio sort it out. 
#: (Sounds like AUDIO_INTERPOLATION_CUBIC)
AUDIO_INTERPOLATION_NONE = 0
#: Perform sharp linear interpolation between samples. 
#: This is the algorithm used by most early DSPs, such as the one in the original 
#: Sound Blaster, and has a pleasing brightness and crispness to it.
AUDIO_INTERPOLATION_LINEAR = 1
#: Perform sharp step interpolation between samples.
#: I'm sure if you go nasty enough, you could find a DSP that sounds like this.
#: This sounds like AUDIO_INTERPOLATION_LINEAR, except with more distortion.
AUDIO_INTERPOLATION_STEP = 2
#: Perform smooth cubic spline interpolation between samples. 
#: This algorithm is used by modern upsampling engines, as it doesn't introduce much 
#: high-frequency noise and can be said to sound more accurate. Who knew "accurate" 
#: was really synonymous with "muddy and awful"?
AUDIO_INTERPOLATION_CUBIC = 3

PLAYBACK_BUFFER = 4096
RESAMPLE_RATE = 44100
RESAMPLE_WIDTH = SAMPLE_WIDTH_INT16_LE


def normalize_audio( source, sample_width ):
    if sample_width == SAMPLE_WIDTH_UINT8:
        return [float( x-128 )/128 for x in array( 'B', source )]
    elif sample_width == SAMPLE_WIDTH_INT8:
        return [float( x )/128 for x in array( 'b', source )]
    elif sample_width == SAMPLE_WIDTH_INT16_LE:
        return [float( x )/32768 for x in array( 'h', source )]
    elif sample_width == SAMPLE_WIDTH_INT32_LE:
        return [float( x )/2147483648 for x in array( 'l', source )]
    return []


def resample_audio( norm_source, sample_rate, interpolation ):
    samp_len = len( norm_source )-1
    new_len = RESAMPLE_RATE*samp_len//sample_rate

    if interpolation == AUDIO_INTERPOLATION_LINEAR:
        return array( 'h', (int( 
            32768*(norm_source[sample_rate*i//RESAMPLE_RATE] + (
                (sample_rate*i % RESAMPLE_RATE)/RESAMPLE_RATE
            )*(
                norm_source[(sample_rate*i//RESAMPLE_RATE)+1]-
                norm_source[sample_rate*i//RESAMPLE_RATE]
            )) 
        ) for i in range( new_len )) ).tobytes()
    elif interpolation == AUDIO_INTERPOLATION_STEP:
        return array( 'h', (int(
            32768*norm_source[sample_rate*i//RESAMPLE_RATE]
        ) for i in range( new_len )) ).tobytes()
    return data


class Wave( mrc.View ):
    def __init__( self, parent, source, channels, sample_width, sample_rate ):
        super( Wave, self ).__init__( parent )
        self._source = source
        self._channels = channels
        self._sample_width = sample_width
        self._sample_rate = sample_rate

    def play( self, interpolation=AUDIO_INTERPOLATION_LINEAR ):
        audio = pyaudio.PyAudio()
        data = b''
        format=self._sample_width[0]
        rate = self._sample_rate

        if interpolation == AUDIO_INTERPOLATION_NONE:
            padding = self._sample_width[1]*(2*PLAYBACK_BUFFER-(len( self._source ) % PLAYBACK_BUFFER))
            data = self._source+padding
        else:
            format = RESAMPLE_WIDTH[0]
            rate=RESAMPLE_RATE

            samp_array = normalize_audio( self._source, self._sample_width )+[0.0]
                
            samp_len = len( self._source )
            new_len = RESAMPLE_RATE*samp_len//self._sample_rate

            padding = RESAMPLE_WIDTH[1]*(2*PLAYBACK_BUFFER-(new_len % PLAYBACK_BUFFER))
            data = resample_audio( samp_array, self._sample_rate, interpolation ) + padding
           
        stream = audio.open( 
            format=format,
            channels=self._channels,
            rate=rate,
            output=True
        )
        stream.write( data )
        stream.stop_stream()
        stream.close()
