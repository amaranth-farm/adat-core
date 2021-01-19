from functools import reduce

def concatenate_lists(lists):
    return reduce(lambda a, b: a + b, lists)

class TestDataGenerator:
    sync_sequence = 10 * [0]
    user_bits = 4 * [0]
    sync = [1]

    @staticmethod
    def postamble(userbits = user_bits):\
        return TestDataGenerator.sync + TestDataGenerator.sync_sequence + TestDataGenerator.sync + userbits

    @staticmethod
    def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    @staticmethod
    def convert_sample(sample24bit):
        bitstring = [ int(b) for b in concatenate_lists(['1' + s for s in TestDataGenerator.chunks("{0:024b}".format(sample24bit), 4)])]
        print (bitstring)
        return bitstring

    @staticmethod
    def generate_adat_frame(sample_8channels):
        frame = concatenate_lists([TestDataGenerator.convert_sample(sample_1ch) for sample_1ch in sample_8channels])
        frame.extend(TestDataGenerator.postamble())
        return frame

def generate_adat_frame(sample_8channels):
    return TestDataGenerator.generate_adat_frame(sample_8channels)

def one_empty_adat_frame():
    return generate_adat_frame(8 * [0])

def generate_one_frame_with_channel_numbers_as_samples():
    return generate_adat_frame(range(8))

def generate_sixteen_frames_with_channel_numbers_in_most_significant_nibble_and_sample_numbers_in_sample():
    samples_8ch = list(TestDataGenerator.chunks([(channelno << 20 | sampleno) for sampleno in range(16) for channelno in range(8)], 8))
    return concatenate_lists([generate_adat_frame(sample_8ch) for sample_8ch in samples_8ch])

def encode_nrzi(input: list) -> list:
    result = [1]
    for bit in input:
        last_bit = result[-1]
        result.append(last_bit if bit == 0 else (~last_bit) & 1)
    return result

if __name__ == "__main__":
    result = encode_nrzi(list(generate_sixteen_frames_with_channel_numbers_in_most_significant_nibble_and_sample_numbers_in_sample()))
    print(str(result))
