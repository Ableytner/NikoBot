from __future__ import annotations

import os

from PIL import Image

from discord import Embed, File, Color

ASSETS_PATH = os.path.join(__file__.rsplit(os.sep, maxsplit=1)[0], "assets")

class Aspect():
    def __init__(self, name: str, keyword: str, cost: int = 10, component1: Aspect = None, component2: Aspect = None) -> None:
        self.name = name
        self.keyword = keyword
        self.cost = cost
        self.component1 = component1
        self.component2 = component2

        assert type(self.name) == str, f"Expected str, got {type(self.name)}({self.name})"
        assert type(self.keyword) == str, f"Expected str, got {type(self.keyword)}({self.keyword})"
        if not self.primal():
            assert type(self.component1) == Aspect, f"Expected Aspect, got {type(self.component1)}({self.component1})"
            assert type(self.component2) == Aspect, f"Expected Aspect, got {type(self.component2)}({self.component2})"

    neighbors: list[Aspect] | None = None

    def construct_neighbors(self, aspects: dict[str, Aspect]) -> None:
        self.neighbors = []
        for aspect in aspects.values():
            if self == aspect.component1 or self == aspect.component2 or self.component1 == aspect or self.component2 == aspect:
                self.neighbors.append(aspect)

    def primal(self) -> bool:
        return (self.component1 == None and self.component2 == None)
    
    def names(self) -> list[str]:
        return [self.name, self.keyword]
    
    def components(self) -> list[Aspect]:
        return [self.component1, self.component2]

    def derives_from(self, aspect: Aspect) -> bool:
        if aspect.name == self.name:
            return True
        if self.primal():
            return False
        return self.component1.derives_from(aspect) or self.component2.derives_from(aspect)

    def embed(self) -> tuple[Embed, File]:
        # get the aspect color
        im = Image.open(f"{ASSETS_PATH}/{self.name.lower()}.png")
        pix = im.load()
        central_rgb = pix[int(im.size[0]/2), int(im.size[1]/2)][:-1:]
        c = 0
        # while the color is black, look at the next pixel
        while all([item < 50 for item in central_rgb]):
            c += 1
            if int(im.size[0]/2+c) >= im.width or int(im.size[1]/2+c) >= im.height:
                break
            central_rgb = pix[int(im.size[0]/2+c), int(im.size[1]/2+c)][:-1:]

        embed_var = Embed(title=self.name, color=Color.from_rgb(*central_rgb))
        file = File(f"{ASSETS_PATH}/{self.name.lower()}.png", filename=f"{self.name.lower()}.png")
        embed_var.set_image(url=f"attachment://{self.name.lower()}.png")
        embed_var.add_field(name="Keyword", value=f"{self.keyword}", inline=False)
        if not self.primal():
            embed_var.add_field(name="Component 1", value=f"{self.component1.name} ({self.component1.keyword})", inline=False)
            embed_var.add_field(name="Component 2", value=f"{self.component2.name} ({self.component2.keyword})", inline=False)
        embed_var.add_field(name="Cost", value=f"{self.cost}", inline=False)
        return embed_var, file

    def __str__(self) -> str:
        return f"{self.name} ({self.keyword})"

    def __repr__(self) -> str:
        return f"{self.name} ({self.keyword})"
