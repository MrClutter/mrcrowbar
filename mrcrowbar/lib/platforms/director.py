
from mrcrowbar import models as mrc
from mrcrowbar.lib.images import base as img
from mrcrowbar.lib.containers import riff
from mrcrowbar import utils

from enum import IntEnum

DIRECTOR_PALETTE_RAW =  '000000111111222222444444555555777777888888aaaaaa'\
                        'bbbbbbddddddeeeeee000011000022000044000055000077'\
                        '0000880000aa0000bb0000dd0000ee001100002200004400'\
                        '00550000770000880000aa0000bb0000dd0000ee00110000'\
                        '220000440000550000770000880000aa0000bb0000dd0000'\
                        'ee00000000330000660000990000cc0000ff003300003333'\
                        '0033660033990033cc0033ff006600006633006666006699'\
                        '0066cc0066ff0099000099330099660099990099cc0099ff'\
                        '00cc0000cc3300cc6600cc9900cccc00ccff00ff0000ff33'\
                        '00ff6600ff9900ffcc00ffff330000330033330066330099'\
                        '3300cc3300ff3333003333333333663333993333cc3333ff'\
                        '3366003366333366663366993366cc3366ff339900339933'\
                        '3399663399993399cc3399ff33cc0033cc3333cc6633cc99'\
                        '33cccc33ccff33ff0033ff3333ff6633ff9933ffcc33ffff'\
                        '6600006600336600666600996600cc6600ff663300663333'\
                        '6633666633996633cc6633ff666600666633666666666699'\
                        '6666cc6666ff6699006699336699666699996699cc6699ff'\
                        '66cc0066cc3366cc6666cc9966cccc66ccff66ff0066ff33'\
                        '66ff6666ff9966ffcc66ffff990000990033990066990099'\
                        '9900cc9900ff9933009933339933669933999933cc9933ff'\
                        '9966009966339966669966999966cc9966ff999900999933'\
                        '9999669999999999cc9999ff99cc0099cc3399cc6699cc99'\
                        '99cccc99ccff99ff0099ff3399ff6699ff9999ffcc99ffff'\
                        'cc0000cc0033cc0066cc0099cc00cccc00ffcc3300cc3333'\
                        'cc3366cc3399cc33cccc33ffcc6600cc6633cc6666cc6699'\
                        'cc66cccc66ffcc9900cc9933cc9966cc9999cc99cccc99ff'\
                        'cccc00cccc33cccc66cccc99ccccccccccffccff00ccff33'\
                        'ccff66ccff99ccffccccffffff0000ff0033ff0066ff0099'\
                        'ff00ccff00ffff3300ff3333ff3366ff3399ff33ccff33ff'\
                        'ff6600ff6633ff6666ff6699ff66ccff66ffff9900ff9933'\
                        'ff9966ff9999ff99ccff99ffffcc00ffcc33ffcc66ffcc99'\
                        'ffccccffccffffff00ffff33ffff66ffff99ffffccffffff'

DIRECTOR_PALETTE = img.from_palette_bytes( bytes.fromhex( DIRECTOR_PALETTE_RAW ), stride=3, order=(0, 1, 2) )


class Rect( mrc.Block ):
    top = mrc.UInt16_BE( 0x00 )
    left = mrc.UInt16_BE( 0x02 )
    bottom = mrc.UInt16_BE( 0x04 )
    right = mrc.UInt16_BE( 0x06 )

    @property
    def width( self ):
        return self.right-self.left

    @property
    def height( self ):
        return self.bottom-self.top

    @property
    def repr( self ):
        return 'top={}, left={}, bottom={}, right={}, width={}, height={}'.format( 
            self.top, self.left, self.bottom, self.right, self.width, self.height )


class SoundCastV4( mrc.Block ):
    pass


class BitmapCastV4( mrc.Block ):
    unk1 = mrc.UInt8( 0x00 )
    unk2 = mrc.Bits( 0x01, 0xf0 )
    pitch = mrc.Bits( 0x01, 0x0fff, size=2 )
    initial_rect = mrc.BlockField( Rect, 0x03 )
    bounding_rect = mrc.BlockField( Rect, 0x0b )
    reg_x = mrc.UInt16_BE( 0x13 )
    reg_y = mrc.UInt16_BE( 0x15 )
    #bpp = mrc.UInt16_BE( 0x17 )
    #unk4 = mrc.Bytes( 0x1a, length=0x24 )
    #name = mrc.Bytes( 0x3e )
    unk4 = mrc.Bytes( 0x17 )

    @property
    def repr( self ):
        #return 'name={}, pitch={}, bpp={}, reg_x={}, reg_y={}, unk1={}, unk2={}'.format( self.name, self.pitch, self.bpp, self.reg_x, self.reg_y, self.unk1, self.unk2 )
        return 'pitch={}, reg_x={}, reg_y={}, unk1={}, unk2={}, unk4={}'.format( self.pitch, self.reg_x, self.reg_y, self.unk1, self.unk2, self.unk4 )


class BitmapCompressor( mrc.Transform ):
    def import_data( self, buffer ):
        result = bytearray()
        pointer = 0
        while (pointer < len( buffer )):
            test = buffer[pointer]
            pointer += 1
            length = test + 1
            if test & 0x80:
                length = ((test ^ 0xff) & 0xff) + 2
                result.extend( (buffer[pointer] for i in range( length )) )
                pointer += 1
            else:
                result.extend( buffer[pointer:pointer+length] )
                pointer += length
        return {'payload': result}


class CastType( IntEnum ):
    NULL =          0x00
    BITMAP =        0x01
    FILM_LOOP =     0x02
    TEXT =          0x03
    PALETTE =       0x04
    PICTURE =       0x05
    SOUND =         0x06
    BUTTON =        0x07
    SHAPE =         0x08
    MOVIE =         0x09
    DIGITAL_VIDEO = 0x0a
    LINGO_SCRIPT =  0x0b
    RTE =           0x0c


class CastV4( mrc.Block ):
    CAST_MAP = {
        CastType.BITMAP: BitmapCastV4,
    }

    size1 =     mrc.UInt16_BE( 0x00 )
    size2 =     mrc.UInt32_BE( 0x02 )
    cast_type = mrc.UInt8( 0x06, enum=CastType )
    detail =    mrc.BlockField( CAST_MAP, 0x07, block_type=mrc.Ref( 'cast_type' ), default_klass=mrc.Unknown )

    @property
    def repr( self ):
        return 'size1: {}, size2: {}, type: {}'.format( self.size1, self.size2, str( self.cast_type ) )


class KeyEntry( mrc.Block ):
    section_index   = mrc.UInt32_P( 0x00 )
    cast_index      = mrc.UInt32_P( 0x04 )
    chunk_id        = mrc.UInt32_P( 0x08 )

    @property
    def repr( self ):
        return 'chunk_id: {}, section_index: {}, cast_index: {}'.format( riff.TagB( self.chunk_id ), self.section_index, self.cast_index )


class KeyV4( mrc.Block ):
    unk1 =          mrc.UInt16_P( 0x00 )
    unk2 =          mrc.UInt16_P( 0x02 )
    unk3 =          mrc.UInt32_P( 0x04 )
    entry_count =   mrc.UInt32_P( 0x08 )
    entries =       mrc.BlockField( KeyEntry, 0x0c, count=mrc.Ref( 'entry_count' ) )
    garbage =       mrc.Bytes( mrc.EndOffset( 'entries' ) )


class MMapEntry( mrc.Block ):
    chunk_id =  mrc.UInt32_P( 0x00 )
    length =    mrc.UInt32_P( 0x04 )
    offset =    mrc.UInt32_P( 0x08 )
    flags =     mrc.UInt16_P( 0x0c )
    unk1 =      mrc.UInt16_P( 0x0e )
    memsize =   mrc.UInt32_P( 0x10 )

    @property
    def repr( self ):
        return 'chunk_id: {}, length: 0x{:08x}, offset: 0x{:08x}, flags: {}'.format( riff.TagB( self.chunk_id ), self.length, self.offset, self.flags )


class MMapV4( mrc.Block ):
    unk1 =      mrc.Bytes( 0x00, length=8 )
    entries_max = mrc.UInt32_P( 0x04 )
    entries_used = mrc.UInt32_P( 0x08 )
    unk2 =      mrc.Const( mrc.Bytes( 0x0c, length=8 ), b'\xff'*8 )
    unk3 =      mrc.UInt32_P( 0x14 )
    entries =    mrc.BlockField( MMapEntry, 0x18, count=mrc.Ref( 'entries_max' ), fill=b'\xaa'*0x14 )
    
    @property
    def repr( self ):
        return 'entries_max: {}, entries_used: {}'.format( self.entries_max, self.entries_used )


class Sord( mrc.Block ):
    unk1 = mrc.Bytes( 0x00, size=0xc )
    count = mrc.UInt32_BE( 0x0c )
    unk2 = mrc.UInt16_BE( 0x10 )
    unk3 = mrc.UInt16_BE( 0x12 )
    index = mrc.UInt16_BE( 0x14, count=mrc.Ref( 'count' ) )


class DirectorV4Map( riff.RIFXMap ):
    CHUNK_MAP = {
        riff.Tag( b'mmap' ): MMapV4,
        riff.Tag( b'KEY*' ): KeyV4,
        riff.Tag( b'Sord' ): Sord,
        riff.Tag( b'CASt' ): CastV4,
    }
DirectorV4Map.CHUNK_MAP[riff.Tag( b'RIFX' )] = DirectorV4Map


class DirectorV4( riff.RIFX ):
    CHUNK_MAP_CLASS = DirectorV4Map


class PJ93( mrc.Block ):
    _endian = 'little'
    
    magic = mrc.Const( mrc.Bytes( 0x00 ), b'PJ93' )
    rifx_offset = mrc.UInt32_P( 0x04 )
    fontmap_offset = mrc.UInt32_P( 0x08 )
    resfork1_offset = mrc.UInt32_P( 0x0c )
    resfork2_offset = mrc.UInt32_P( 0x10 )
    graphics_dll_offset = mrc.UInt32_P( 0x14 )
    sound_dll_offset = mrc.UInt32_P( 0x18 )
    rifx_offset_dup = mrc.UInt32_P( 0x1c )
    
