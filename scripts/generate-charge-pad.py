#!/usr/bin/env python3
"""Build the original in-arena charge pad, with no imported artwork."""
import base64
import json
from pathlib import Path
import struct

data = bytearray()
doc = dict(asset=dict(version="2.0", generator="Screech charge pad"),
           scene=0, scenes=[dict(nodes=[0])], nodes=[dict(mesh=0)],
           meshes=[dict(primitives=[])], buffers=[], bufferViews=[], accessors=[], materials=[])

def accessor(values, packing, kind, bounds=False):
    while len(data) % 4:
        data.append(0)
    start = len(data)
    for value in values:
        data.extend(struct.pack("<" + packing, *value))
    view = len(doc["bufferViews"])
    doc["bufferViews"].append(dict(buffer=0, byteOffset=start, byteLength=len(data)-start))
    item = dict(bufferView=view, componentType=5123 if packing == "H" else 5126, count=len(values), type=kind)
    if bounds:
        item.update(min=list(map(min, zip(*values))), max=list(map(max, zip(*values))))
    doc["accessors"].append(item)
    return len(doc["accessors"]) - 1

def boxes(name, color, glow, shapes):
    p, n, uv, idx = [], [], [], []
    for center, size in shapes:
        for a, b, c in [(0,1,2), (1,2,0), (2,0,1)]:
            for sign in (1,-1):
                start = len(p)
                for u,v in [(-1,-1),(1,-1),(1,1),(-1,1)]:
                    vtx = list(center)
                    vtx[a] += sign * size[a] / 2
                    vtx[b] += u * size[b] / 2
                    vtx[c] += v * size[c] / 2
                    p.append(tuple(vtx))
                    n.append(tuple(sign if i == a else 0 for i in range(3)))
                    uv.append(((u+1)/2,(v+1)/2))
                order = (0,1,2,0,2,3) if sign > 0 else (0,2,1,0,3,2)
                idx.extend((start+i,) for i in order)
    material = len(doc["materials"])
    doc["materials"].append(dict(name=name, emissiveFactor=glow,
        pbrMetallicRoughness=dict(baseColorFactor=color+[1], metallicFactor=0.25, roughnessFactor=0.6)))
    doc["meshes"][0]["primitives"].append(dict(material=material, indices=accessor(idx,"H","SCALAR"),
        attributes=dict(POSITION=accessor(p,"3f","VEC3",True), NORMAL=accessor(n,"3f","VEC3"),
                        TEXCOORD_0=accessor(uv,"2f","VEC2"))))

boxes("graphite housing",[.08,.11,.14],[0,0,0],[((0,.05,0),(3.25,.1,3.25))])
boxes("cyan running lights",[.04,.8,.92],[.03,.6,.8],
      [((x,.13,0),(.14,.06,3.10)) for x in (-1.48,1.48)] +
      [((0,.13,z),(2.82,.06,.14)) for z in (-1.48,1.48)])
boxes("amber plus",[1,.55,.07],[.9,.3,.012],
      [((0,.14,0),(.36,.08,1.65)), ((-.49,.14,0),(.61,.08,.36)), ((.49,.14,0),(.61,.08,.36))])
doc["buffers"].append(dict(byteLength=len(data), uri="data:application/octet-stream;base64,"+
                                base64.b64encode(data).decode("ascii")))
Path(__file__).resolve().parents[1].joinpath("data/charge-pad.gltf").write_text(json.dumps(doc, separators=(",",":"))+"\n")
