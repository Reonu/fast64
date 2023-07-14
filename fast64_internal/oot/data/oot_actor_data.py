from os import path
from dataclasses import dataclass
from .oot_getters import getXMLRoot
from .oot_data import OoT_BaseElement


@dataclass
class OoT_ParameterElement:
    type: str # bool, enum, type, property, etc...
    index: int
    mask: int
    name: str
    subType: str # used for <Flag> and <Collectible>
    target: str
    tiedTypes: list[int]
    items: list[tuple[int, str]] # for <Type> and <Enum>, int is "Value"/"Params" and str is the name
    

@dataclass
class OoT_ListElement:
    key: str
    name: str
    value: int


@dataclass
class OoT_ActorElement(OoT_BaseElement):
    category: str
    tiedObjects: list[str]
    params: list[OoT_ParameterElement]


class OoT_ActorData:
    """Everything related to OoT Actors"""

    def __init__(self):
        # Path to the ``ActorList.xml`` file
        actorXML = path.dirname(path.abspath(__file__)) + "/xml/ActorList.xml"
        actorRoot = getXMLRoot(actorXML)

        # general actor list
        self.actorList: list[OoT_ActorElement] = []

        # list elements
        self.chestItems: list[OoT_ListElement] = []
        self.collectibleItems: list[OoT_ListElement] = []
        self.messageItems: list[OoT_ListElement] = []

        listNameToList = {
            "Chest Content": self.chestItems,
            "Collectibles": self.collectibleItems,
            "Elf_Msg Message ID": self.messageItems,
        }

        for elem in actorRoot.iterfind("List"):
            listName = elem.get("Name")

            if listName is not None:
                for item in elem:
                    listNameToList[listName].append(
                        OoT_ListElement(item.get("Key"), item.get("Name"), int(item.get("Value"), base=16))
                    )

        for actor in actorRoot.iterfind("Actor"):
            tiedObjects = []
            objKey = actor.get("ObjectKey")
            actorName = f"{actor.attrib['Name']} - {actor.attrib['ID'].removeprefix('ACTOR_')}"
            
            if objKey is not None:  # actors don't always use an object
                tiedObjects = objKey.split(",")

            # parameters
            params: list[OoT_ParameterElement] = []
            for elem in actor:
                elemType = elem.tag

                if elemType != "Notes":
                    items: list[tuple[int, str]] = []

                    if elemType == "Type" or elemType == "Enum":
                        for item in elem:
                            key = "Params" if elemType == "Type" else "Value"
                            name = item.text.strip() if elemType == "Type" else item.get("Name")

                            if key is not None and name is not None:
                                items.append((int(item.get(key), base=16), name))

                    # not every actor have parameters tied to a specific actor type
                    tiedTypes = elem.get("TiedActorTypes")
                    tiedTypeList = []
                    if tiedTypes is not None:
                        tiedTypeList = [int(val, base=16) for val in tiedTypes.split(",")]

                    defaultName = f"{elem.get('Type')} {elemType}"
                    params.append(
                        OoT_ParameterElement(
                            elemType,
                            int(elem.get("Index", "1")),
                            int(elem.get("Mask", "0xFFFF"), base=16),
                            elem.get("Name", defaultName if not "None" in defaultName else elemType),
                            elem.get("Type"),
                            elem.get("Target", "Params"),
                            tiedTypeList,
                            items
                        )
                    )

            self.actorList.append(
                OoT_ActorElement(
                    actor.attrib["ID"],
                    actor.attrib["Key"],
                    actorName,
                    int(actor.attrib["Index"]),
                    actor.attrib["Category"],
                    tiedObjects,
                    params
                )
            )

        self.actorsByKey = {actor.key: actor for actor in self.actorList}
        self.actorsByID = {actor.id: actor for actor in self.actorList}

        self.chestItemByKey = {elem.key: elem for elem in self.chestItems}
        self.collectibleItemsByKey = {elem.key: elem for elem in self.collectibleItems}
        self.messageItemsByKey = {elem.key: elem for elem in self.messageItems}

        # list of tuples used by Blender's enum properties
        lastIndex = max(1, *(actor.index for actor in self.actorList))
        self.ootEnumActorID = [("None", f"{i} (Deleted from the XML)", "None") for i in range(lastIndex)]
        self.ootEnumActorID.insert(0, ("Custom", "Custom Actor", "Custom"))
        for actor in self.actorList:
            self.ootEnumActorID[actor.index] = (actor.id, actor.name, actor.id)

        self.ootEnumChestContent = [(elem.key, elem.name, elem.key) for elem in self.chestItems]
        self.ootEnumCollectibleItems = [(elem.key, elem.name, elem.key) for elem in self.collectibleItems]
        self.ootEnumNaviMessageData = [(elem.key, elem.name, elem.key) for elem in self.messageItems]
