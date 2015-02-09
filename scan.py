#!/usr/bin/python

GQRX_IP_ADDRESS = "127.0.0.1:7356"

FREQLIST = [
    # frequency, threshold, description
    (461.7125e6, -70, "RochRad 01"),
    (462.0375e6, -70, "RochRad 02"),
    (463.2375e6, -70, "RochRad 03"),
    (464.5875e6, -70, "RochRad 04"),
    (462.0875e6, -70, "RochRad 05"),
    (461.4125e6, -70, "RochRad 06"),
    (461.8375e6, -70, "RochRad 07"),
    (463.7875e6, -70, "RochRad 08"),
    (461.5000e6, -70, "FlwrCty 01"),
    (463.9500e6, -70, "FlwrCty 02"),
    (464.1750e6, -70, "FlwrCty 03"),
    (461.1500e6, -70, "FlwrCty 05"),
    (461.2750e6, -70, "FlwrCty 06"),
    (453.6750e6, -70, "MCC-B BldgSv"),
    (453.2000e6, -70, "MCC-B Safety"),
    (444.4000e6, -70, "W2RFC Repeater"),
    (463.4125e6, -70, "RIT Crew 1"),
    (468.4125e6, -70, "RIT Crew 2"),
    (864.2125e6, -60, "RIT Dispatch"),
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
    sys.stdout.write("\x1B]0;%s\x07" % (text, GQRX_IP_ADDRESS))
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

        # Main loop.
        while True:

            # Shuffle the frequency list: mixes things up a bit, and also
            # helps minimize VCO retunes, oddly enough
            random.shuffle(FREQLIST)

            for freq, threshold, chname in FREQLIST:
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
