#   Copyright (c) 2016, Xilinx, Inc.
#   All rights reserved.
# 
#   Redistribution and use in source and binary forms, with or without 
#   modification, are permitted provided that the following conditions are met:
#
#   1.  Redistributions of source code must retain the above copyright notice, 
#       this list of conditions and the following disclaimer.
#
#   2.  Redistributions in binary form must reproduce the above copyright 
#       notice, this list of conditions and the following disclaimer in the 
#       documentation and/or other materials provided with the distribution.
#
#   3.  Neither the name of the copyright holder nor the names of its 
#       contributors may be used to endorse or promote products derived from 
#       this software without specific prior written permission.
#
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
#   THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
#   PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR 
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
#   EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, 
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
#   OR BUSINESS INTERRUPTION). HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, 
#   WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR 
#   OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF 
#   ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


from pynq import MMIO
from pynq import PL

__author__ = "Graham Schelle"
__copyright__ = "Copyright 2016, Xilinx"
__email__ = "pynq_support@xilinx.com"


RGBLEDS_XGPIO_OFFSET = 0
RGB_CLEAR = 0
RGB_BLUE = 1
RGB_GREEN = 2
RGB_CYAN = 3
RGB_RED = 4
RGB_MAGENTA = 5
RGB_YELLOW = 6
RGB_WHITE = 7


class RGBLED(object):
    """This class controls the onboard RGB LEDs.

    Attributes
    ----------
    index : int
        The index of the RGB LED. Can be an arbitrary value.
    offset : int
        When greater than 0, it will be used as offset to access the specific
        RGBLED, instead of relying on the global value `_rgbleds_start_index`.
    _mmio : MMIO
        Shared memory map for the RGBLED GPIO controller.
    _rgbleds_val : int
        Global value of the RGBLED GPIO pins.
    _rgbleds_start_index : int
        Global value representing the lowest index for RGB LEDs
    """
    _mmio = None
    _rgbleds_val = 0
    _rgbleds_start_index = float("inf")

    def __init__(self, index, ip_name="rgbleds_gpio",
                 offset=0):
        """Create a new RGB LED object.
        
        Parameters
        ----------
        index : int
            Index of the RGBLED, Can be an arbitrary value.
            The smallest index given will set the global value
            `_rgbleds_start_index`, unless a valid `offset` is given.
        ìp_name : str
            Name of the IP in  the `ip_dict`. Defaults to "rgbleds_gpio".
        offset : int
            If defined, will be used as offset to access the specific RGBLED,
            instead of relying on the global value `_rgbleds_start_index`.
        """

        self.index = index
        if RGBLED._mmio is None:
            base_addr = PL.ip_dict[ip_name]["phys_addr"]
            RGBLED._mmio = MMIO(base_addr, 16)
        if offset == 0 and index < RGBLED._rgbleds_start_index:
            RGBLED._rgbleds_start_index = index
        if offset < 0:
            raise ValueError("Offset cannot be a negative value.")
        if offset % 4 != 0:
            raise ValueError("Offset must be a multiple of 4.")
        self._offset = offset
        self._val = 0

    def on(self, color):
        """Turn on a single RGB LED with a color value (see color constants).
        
        Parameters
        ----------
        color : int
           Color of RGB specified by a 3-bit RGB integer value.
        
        Returns
        -------
        None
        
        """
        if color not in range(8):
            raise ValueError("color should be an integer value from 0 to 7.")

        if self._offset > 0:
            self._val = self._val & ~0x7 | color
            self._set_rgbleds_value(self._val, self._offset)
        else:
            rgb_mask = 0x7 << ((self.index-RGBLED._rgbleds_start_index)*3)
            new_val = (RGBLED._rgbleds_val & ~rgb_mask) | \
                      (color << ((self.index-RGBLED._rgbleds_start_index)*3))
            self._set_rgbleds_value(new_val)

    def off(self):
        """Turn off a single RGBLED.
        
        Returns
        -------
        None
        
        """
        if self._offset > 0:
            self._val = self._val & ~0x7
            self._set_rgbleds_value(self._val, self._offset)
        else:
            rgb_mask = 0x7 << ((self.index-RGBLED._rgbleds_start_index)*3)
            new_val = RGBLED._rgbleds_val & ~rgb_mask
            self._set_rgbleds_value(new_val)
        
    def write(self, color):
        """Set the RGBLED state according to the input value.

        Parameters
        ----------
        color : int
            Color of RGB specified by a 3-bit RGB integer value.
            
        Returns
        -------
        None
        
        """
        self.on(color)

    def read(self):
        """Retrieve the RGBLED state.

        Returns
        -------
        int
            The color value stored in the RGBLED.
            
        """
        if self._offset > 0:
            return self._val
        return (RGBLED._rgbleds_val >>
                ((self.index-RGBLED._rgbleds_start_index)*3)) & 0x7

    @staticmethod
    def _set_rgbleds_value(value, offset=0):
        """Set the state of all RGBLEDs.
        
        Note
        ----
        This function should not be used directly. User should call 
        `on()`, `off()`, instead.
        
        Parameters
        ----------
        value : int 
            The value of all the RGBLEDs encoded in a single variable.
            If `offset` is specified, it only represents the value of the 
            single RGBLED.
        offset : int
            If specified, it will be used as offset to access the RGBLED shared
            memory map. This will prevent the global value `_rgbleds_val` from
            being updated.

        """
        if offset < 0:
            raise ValueError("Offset cannot be a negative value.")
        if offset % 4 != 0:
            raise ValueError("Offset must be a multiple of 4.")
        if offset == 0:
            RGBLED._rgbleds_val = value
        RGBLED._mmio.write(RGBLEDS_XGPIO_OFFSET + offset, value)
