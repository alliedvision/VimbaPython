"""BSD 2-Clause License

Copyright (c) 2019, Allied Vision Technologies GmbH
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import itertools

from typing import Dict, Tuple
from .c_binding import VmbUint32, VmbUint64, VmbHandle, VmbFeatureInfo
from .c_binding import call_vimba_c, byref, sizeof, create_string_buffer, VimbaCError
from .feature import FeaturesTuple, FeatureTypes, FeatureTypeTypes
from .error import VimbaFeatureError
from .util import TraceEnable

__all__ = [
    'filter_affected_features',
    'filter_selected_features',
    'filter_features_by_name',
    'filter_features_by_type',
    'filter_features_by_category',
    'attach_feature_accessors',
    'remove_feature_accessors',
    'read_memory',
    'write_memory',
    'read_registers',
    'write_registers'
]


@TraceEnable()
def filter_affected_features(feats: FeaturesTuple, feat: FeatureTypes) -> FeaturesTuple:
    """Search for all Features affected by a given feature within a feature set.

    Arguments:
        feats: Feature set to search in.
        feat: Feature that might affect Features within 'feats'.

    Returns:
        A set of all features that are affected by 'feat'.

    Raises:
        VimbaFeatureError if 'feat' is not stored within 'feats'.
    """

    if feat not in feats:
        raise VimbaFeatureError('Feature \'{}\' not in given Features'.format(feat.get_name()))

    result = []

    if feat.has_affected_features():
        feats_count = VmbUint32()
        feats_handle = feat._handle
        feats_name = feat._info.name

        # Query affected features from given Feature
        call_vimba_c('VmbFeatureListAffected', feats_handle, feats_name, None, 0,
                     byref(feats_count), sizeof(VmbFeatureInfo))

        feats_found = VmbUint32(0)
        feats_infos = (VmbFeatureInfo * feats_count.value)()

        call_vimba_c('VmbFeatureListAffected', feats_handle, feats_name, feats_infos, feats_count,
                     byref(feats_found), sizeof(VmbFeatureInfo))

        # Search affected features in given feature set
        for info, feature in itertools.product(feats_infos[:feats_found.value], feats):
            if info.name == feature._info.name:
                result.append(feature)

    return tuple(result)


@TraceEnable()
def filter_selected_features(feats: FeaturesTuple, feat: FeatureTypes) -> FeaturesTuple:
    """Search for all Features selected by a given feature within a feature set.

    Arguments:
        feats: Feature set to search in.
        feat: Feature that might select Features within 'feats'.

    Returns:
        A set of all features that are selected by 'feat'.

    Raises:
        VimbaFeatureError if 'feat' is not stored within 'feats'.
    """
    if feat not in feats:
        raise VimbaFeatureError('Feature \'{}\' not in given Features'.format(feat.get_name()))

    result = []

    if feat.has_selected_features():
        feats_count = VmbUint32()
        feats_handle = feat._handle
        feats_name = feat._info.name

        # Query selected features from given feature
        call_vimba_c('VmbFeatureListSelected', feats_handle, feats_name, None, 0,
                     byref(feats_count), sizeof(VmbFeatureInfo))

        feats_found = VmbUint32(0)
        feats_infos = (VmbFeatureInfo * feats_count.value)()

        call_vimba_c('VmbFeatureListSelected', feats_handle, feats_name, feats_infos, feats_count,
                     byref(feats_found), sizeof(VmbFeatureInfo))

        # Search selected features in given feature set
        for info, feature in itertools.product(feats_infos[:feats_found.value], feats):
            if info.name == feature._info.name:
                result.append(feature)

    return tuple(result)


@TraceEnable()
def filter_features_by_name(feats: FeaturesTuple, feat_name: str):
    """Search for a feature with a specific name within a feature set.

    Arguments:
        feats: Feature set to search in.
        feat_name: Feature name to look for.

    Returns:
        The Feature with the name 'feat_name' or None if lookup failed
    """
    filtered = [feat for feat in feats if feat_name == feat.get_name()]
    return filtered.pop() if filtered else None


@TraceEnable()
def filter_features_by_type(feats: FeaturesTuple, feat_type: FeatureTypeTypes) -> FeaturesTuple:
    """Search for all features with a specific type within a given feature set.

    Arguments:
        feats: Feature set to search in.
        feat_type: Feature Type to search for

    Returns:
        A set of all features of type 'feat_type' in 'feats'. If no matching type is found an
        empty set is returned.
    """
    return tuple([feat for feat in feats if type(feat) == feat_type])


@TraceEnable()
def filter_features_by_category(feats: FeaturesTuple, category: str) -> FeaturesTuple:
    """Search for all features of a given category.

    Arguments:
        feats: Feature set to search in.
        category: Category to filter for

    Returns:
        A set of all features of category 'category' in 'feats'. If no matching type is found an
        empty set is returned.
    """
    return tuple([feat for feat in feats if feat.get_category() == category])


@TraceEnable()
def attach_feature_accessors(obj, feats: FeaturesTuple):
    """Attach all Features in feats to obj under the feature name.

    Arguments:
        obj: Object feats should be attached on.
        feats: Features to attach.
    """
    BLACKLIST = (
        'PixelFormat',   # PixelFormats have special access methods.
    )

    for feat in feats:
        feat_name = feat.get_name()
        if feat_name not in BLACKLIST:
            setattr(obj, feat_name, feat)


@TraceEnable()
def remove_feature_accessors(obj, feats: FeaturesTuple):
    """Remove all Features in feats from obj.

    Arguments:
        obj: Object, feats should be removed from.
        feats: Features to remove.
    """
    for feat in feats:
        try:
            delattr(obj, feat.get_name())

        except AttributeError:
            pass


@TraceEnable()
def read_memory(handle: VmbHandle, addr: int, max_bytes: int) -> bytes:  # coverage: skip
    """Read a byte sequence from a given memory address.

    Arguments:
        handle: Handle on entity that allows raw memory access.
        addr: Starting address to read from.
        max_bytes: Maximum number of bytes to read from addr.

    Returns:
        Read memory contents as bytes.

    Raises:
        ValueError if addr is negative
        ValueError if max_bytes is negative.
        ValueError if the memory access was invalid.
    """
    # Note: Coverage is skipped. Function is untestable in a generic way.
    _verify_addr(addr)
    _verify_size(max_bytes)

    buf = create_string_buffer(max_bytes)
    bytesRead = VmbUint32()

    try:
        call_vimba_c('VmbMemoryRead', handle, addr, max_bytes, buf, byref(bytesRead))

    except VimbaCError as e:
        msg = 'Memory read access at {} failed with C-Error: {}.'
        raise ValueError(msg.format(hex(addr), repr(e.get_error_code()))) from e

    return buf.value[:bytesRead.value]


@TraceEnable()
def write_memory(handle: VmbHandle, addr: int, data: bytes):  # coverage: skip
    """ Write a byte sequence to a given memory address.

    Arguments:
        handle: Handle on entity that allows raw memory access.
        addr: Address to write the content of 'data' too.
        data: Byte sequence to write at address 'addr'.

    Raises:
        ValueError if addr is negative.
        ValueError if the memory access was invalid.
    """
    # Note: Coverage is skipped. Function is untestable in a generic way.
    _verify_addr(addr)

    bytesWrite = VmbUint32()

    try:
        call_vimba_c('VmbMemoryWrite', handle, addr, len(data), data, byref(bytesWrite))

    except VimbaCError as e:
        msg = 'Memory write access at {} failed with C-Error: {}.'
        raise ValueError(msg.format(hex(addr), repr(e.get_error_code()))) from e


@TraceEnable()
def read_registers(handle: VmbHandle, addrs: Tuple[int, ...]) -> Dict[int, int]:  # coverage: skip
    """Read contents of multiple registers.

    Arguments:
        handle: Handle on entity providing registers to access.
        addrs: Sequence of addresses that should be read iteratively.

    Return:
        Dictionary containing a mapping from given address to the read register values.

    Raises:
        ValueError if any address in addrs is negative.
        ValueError if the register access was invalid.
    """
    # Note: Coverage is skipped. Function is untestable in a generic way.
    for addr in addrs:
        _verify_addr(addr)

    size = len(addrs)
    valid_reads = VmbUint32()

    c_addrs = (VmbUint64 * size)()
    c_values = (VmbUint64 * size)()

    for i, addr in enumerate(addrs):
        c_addrs[i] = addr

    try:
        call_vimba_c('VmbRegistersRead', handle, size, c_addrs, c_values, byref(valid_reads))

    except VimbaCError as e:
        msg = 'Register read access failed with C-Error: {}.'
        raise ValueError(msg.format(repr(e.get_error_code()))) from e

    return dict(zip(c_addrs, c_values))


@TraceEnable()
def write_registers(handle: VmbHandle, addrs_values: Dict[int, int]):  # coverage: skip
    """Write data to multiple Registers.

    Arguments:
        handle: Handle on entity providing registers to access.
        addrs_values: Mapping between Register addresses and the data to write.

    Raises:
        ValueError if any address in addrs_values is negative.
        ValueError if the register access was invalid.
    """
    # Note: Coverage is skipped. Function is untestable in a generic way.
    for addr in addrs_values:
        _verify_addr(addr)

    size = len(addrs_values)
    valid_writes = VmbUint32()

    addrs = (VmbUint64 * size)()
    values = (VmbUint64 * size)()

    for i, addr in enumerate(addrs_values):
        addrs[i] = addr
        values[i] = addrs_values[addr]

    try:
        call_vimba_c('VmbRegistersWrite', handle, size, addrs, values, byref(valid_writes))

    except VimbaCError as e:
        msg = 'Register write access failed with C-Error: {}.'
        raise ValueError(msg.format(repr(e.get_error_code()))) from e


def _verify_addr(addr: int):  # coverage: skip
    # Note: Coverage is skipped. Function is untestable in a generic way.
    if addr < 0:
        raise ValueError('Given Address {} is negative'.format(addr))


def _verify_size(size: int):  # coverage: skip
    # Note: Coverage is skipped. Function is untestable in a generic way.
    if size < 0:
        raise ValueError('Given size {} is negative'.format(size))
