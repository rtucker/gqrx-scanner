#!/usr/bin/python

GQRX_IP_ADDRESS = "127.0.0.1:7356"

FREQLIST = [
    # weight, frequency, threshold, description
    (1, 462.5625e6, -70, "FRS 1"),
    (1, 462.5875e6, -70, "FRS 2"),
    (1, 462.6125e6, -70, "FRS 3"),
    (1, 462.6375e6, -70, "FRS 4"),
    (1, 462.6625e6, -70, "FRS 5"),
    (1, 462.6875e6, -70, "FRS 6"),
    (1, 462.7125e6, -70, "FRS 7"),
    (1, 467.5625e6, -70, "FRS 8"),
    (1, 467.5875e6, -70, "FRS 9"),
    (1, 467.6125e6, -70, "FRS 10"),
    (1, 467.6375e6, -70, "FRS 11"),
    (1, 467.6625e6, -70, "FRS 12"),
    (1, 467.6875e6, -70, "FRS 13"),
    (1, 467.7125e6, -70, "FRS 14"),
    (1, 462.5500e6, -70, "GMRS 1"),
    (1, 462.5750e6, -70, "GMRS 2"),
    (1, 462.6000e6, -70, "GMRS 3"),
    (1, 462.6250e6, -70, "GMRS 4"),
    (1, 462.6500e6, -70, "GMRS 5"),
    (1, 462.6750e6, -70, "GMRS 6"),
    (1, 462.7000e6, -70, "GMRS 7"),
    (1, 462.7250e6, -70, "GMRS 8"),
    (1, 467.5500e6, -70, "GMRS 1 in"),
    (1, 467.5750e6, -70, "GMRS 2 in"),
    (1, 467.6000e6, -70, "GMRS 3 in"),
    (1, 467.6250e6, -70, "GMRS 4 in"),
    (1, 467.6500e6, -70, "GMRS 5 in"),
    (1, 467.6750e6, -70, "GMRS 6 in"),
    (1, 467.7000e6, -70, "GMRS 7 in"),
    (1, 467.7250e6, -70, "GMRS 8 in"),
    (3, 461.7125e6, -70, "RochRad 01"),
    (3, 462.0375e6, -70, "RochRad 02"),
    (7, 463.2375e6, -70, "RochRad 03"),
    (7, 464.5875e6, -70, "RochRad 04"),
    (3, 462.0875e6, -70, "RochRad 05"),
    (3, 461.4125e6, -70, "RochRad 06"),
    (3, 461.8375e6, -70, "RochRad 07"),
    (3, 463.7875e6, -70, "RochRad 08"),
    (2, 461.5000e6, -70, "FlwrCty 01"),
    (2, 463.9500e6, -70, "FlwrCty 02"),
    (2, 464.1750e6, -70, "FlwrCty 03"),
    (2, 461.1500e6, -70, "FlwrCty 05"),
    (2, 461.2750e6, -70, "FlwrCty 06"),
    (1, 452.9375e6, -70, "Rail ETD Engine"),
    (1, 457.9375e6, -70, "Rail ETD Train"),
    (1, 453.6750e6, -70, "MCC-B BldgSv"),
    (1, 453.2000e6, -70, "MCC-B Safety"),
    (1, 444.4000e6, -70, "W2RFC Repeater"),
    (1, 463.4125e6, -70, "RIT Crew 1"),
    (1, 468.4125e6, -70, "RIT Crew 2"),
    (0, 864.2125e6, -60, "RIT Dispatch"),
]

import Hamlib
import random
import sys
import time


class NetRig(object):

    rig = None

    def __init__(self, addr):
        self.rig = Hamlib.Rig(Hamlib.RIG_MODEL_NETRIGCTL)
        self.rig.set_conf("rig_pathname", addr)
        self.rig.open()

        self.rig.rig.state.has_get_level = Hamlib.RIG_LEVEL_STRENGTH

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.rig.close()

    def rssi(self):
        return self.rig.get_level_i(Hamlib.RIG_LEVEL_STRENGTH)


def set_title(text):
    sys.stdout.write("\x1B]0;%s\x07" % text)
    sys.stdout.flush()


def main():
    Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)
    #Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_TRACE)

    set_title("scan.py: initializing")
    print("Beginning scan sequence: %s" % GQRX_IP_ADDRESS)

    # Connect to the GQRX server
    with NetRig(GQRX_IP_ADDRESS) as gqrx:

        # Print header text
        print("Freq MHz\tdBm\tAcq\tSecs\tChannel")

        window_title_stale = True

        # Run through the master frequency list and apply the weightings
        freqs = []
        for weight, freq, threshold, chname in FREQLIST:
            while weight > 0:
                freqs.append((freq, threshold, chname))
                weight -= 1

        # Main loop.
        while True:

            # Shuffle the frequency list: mixes things up a bit, and also
            # helps minimize VCO retunes, oddly enough
            random.shuffle(freqs)

            for freq, threshold, chname in freqs:
                # Clear the status line
                sys.stdout.write('\r' + ' '*80)
                # Change our frequency then wait a bit
                gqrx.rig.set_freq(freq)
                time.sleep(0.1)

                # Reset the window title to a generic thing if we're
                # not locked onto a signal.
                if window_title_stale:
                    set_title("<scan>")
                    window_title_stale = False

                # Start off taking one pass through the dwell loop
                rx_active = False
                acq_time = time.time()
                dwell_until = acq_time + 0.01

                while rx_active or (dwell_until > time.time()):
                    # Calculate the RSSI and update our status variables
                    my_rssi = gqrx.rssi()
                    rx_duration = time.time() - acq_time
                    rx_active = my_rssi > threshold

                    # Tell the user what's up
                    if rx_active and not window_title_stale:
                        set_title(chname)
                        window_title_stale = True

                    sys.stdout.write('\r%4.4f\t%4d\t%s\t%3.1f\t%s' % (
                        (freq/1e6), my_rssi, '*' if rx_active else 'x',
                        rx_duration, chname))
                    sys.stdout.flush()

                    # If we're actively receiving and have been for more than
                    # a second, latch onto this channel for a little bit in
                    # case someone responds.
                    if rx_active and rx_duration > 1:
                            dwell_until = time.time() + 1.5

                    # Sleep for a moment to avoid churning.
                    time.sleep(0.01)


if __name__ == '__main__':
    main()
