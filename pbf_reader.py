import zlib, six, os

# WIRE types
wire_types = {
    "VARINT": 0, # varint: int32, int64, uint32, uint64, sint32, sint64, bool, enum
    "FIXED64": 1, # 64-bit: double, fixed64, sfixed64
    "BYTES": 2, # length-delimited: string, bytes, embedded messages, packed repeated fields
    "FIXED32": 5 # 32-bit: float, fixed32, sfixed32
}

wire_type_values = wire_types.values()

class PBFReader(object):
    def __init__(self,buffer):
        self.buffer = buffer
        self.pos = 0
        self.length = len(self.buffer)
        self.tag = 0
        self.wire_type = 99
        self.val = 0

    def varint(self):
        mask = (1 << 64) - 1
        result_type = long
        result = 0
        shift = 0
        while 1:
            b = six.indexbytes(self.buffer, self.pos)
            result |= ((b & 0x7f) << shift)
            self.pos += 1
            if not (b & 0x80):
                result &= mask
                result = result_type(result)
                return result
            shift += 7
            if shift >= 64:
                raise Exception('Too many bytes when decoding varint.')

    def skip_varint(self):
        while ord(self.buffer[self.pos:self.pos+1]) & 0x80:
            self.pos += 1
        self.pos += 1
        if self.pos > self.length:
            raise Exception('Truncated message.')

    def view(self):
        assert(self.tag != 0 and "call next() before accessing field value");
        assert(self.wire_type == wire_types['BYTES'] and "not of type string, bytes or message");
        val = self.varint()
        self.skip_bytes(val)
        return self.buffer[self.pos-val:self.pos]

    def next(self):
        if (self.pos >= self.length):
            return False
        self.val = self.varint()
        self.tag = self.val >> 3
        assert(((self.tag > 0 and self.tag < 19000) or (self.tag > 19999 and self.tag <= ((1 << 29) - 1))) and "tag out of range");
        self.wire_type = self.val & 0x07;
        if not self.wire_type in wire_type_values:
            raise(TypeError("invalid wire type: %s", self.wire_type))
        return True

    def get_string(self):
        return self.view()

    def get_tag(self):
        return self.tag

    def get_wire_type(self):
        return self.wire_type

    def skip_bytes(self,size):
        if size + self.pos > self.length:
            raise Exception("invalid skip %s %s %s",size,self.pos,self.length)
        self.pos += size;

    def get_packed_uint32(self):
        assert(self.tag != 0 and "call next() before accessing field value");
        assert(self.wire_type == wire_types['BYTES'] and "not of type string, bytes or message");
        array = [];
        val = self.varint()
        end = val + self.pos;
        while self.pos < end:
            int_val = self.varint()
            array.append(int(int_val))
        return array

    def skip(self):
        assert(self.tag != 0 and "call next() before calling skip()");
        if self.wire_type == wire_types['VARINT']:
            self.skip_varint()
        elif self.wire_type == wire_types['BYTES']:
            self.skip_bytes(self.varint());
        elif self.wire_type == wire_types['FIXED32']:
            self.skip_bytes(4);
        elif self.wire_type == wire_types['FIXED64']:
            self.skip_bytes(8);
        else:
            raise(TypeError('Unimplemented wire_type: %s ', wire_type));
        return self.pos;
