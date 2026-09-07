import json
import time
from deep_translator import GoogleTranslator

# ============================================================
# ASK ORCA - MULTILINGUAL QUESTION DATASET GENERATOR
# ============================================================

LANGUAGES = {
    "en": "en",
    "hi": "hi",
    "mr": "mr",
    "gu": "gu",
    "bn": "bn",
    "ta": "ta",
    "te": "te",
    "kn": "kn",
    "ml": "ml",
    "or": "or",
    "pa": "pa"
}

# ============================================================
# ALL MAJOR ORCA INTENTS
# ============================================================

QUESTIONS = {

# ------------------------------------------------------------
# WEATHER
# ------------------------------------------------------------

"weather_current": [
    "What is the current weather at my location?",
    "How is the weather right now?",
    "What are the current weather conditions?",
    "Tell me the current weather.",
    "What is the weather like near me?",
    "How is the weather at my boat location?",
    "Give me the current weather update.",
    "What are the weather conditions near my boat?",
    "Is the weather good right now?",
    "Is the current weather safe?"
],

"weather_forecast": [
    "What will the weather be today?",
    "What will the weather be tomorrow?",
    "Give me the weather forecast.",
    "Give me the next 24 hour weather forecast.",
    "What weather should I expect today?",
    "What weather conditions are expected?",
    "Will the weather change today?",
    "What is the marine weather forecast?",
    "Will the weather become dangerous?",
    "What weather is expected near my location?"
],

"rain": [
    "Is it raining now?",
    "Will it rain today?",
    "Will there be rain near me?",
    "Is heavy rain expected?",
    "Will there be heavy rainfall?",
    "Should I expect rain?",
    "Is rain expected at sea?",
    "Will rain affect my fishing trip?",
    "Is there a chance of rain?",
    "How much rain is expected?"
],

"wind": [
    "What is the current wind speed?",
    "How strong is the wind?",
    "Is the wind strong?",
    "What is the wind direction?",
    "Which direction is the wind coming from?",
    "Are strong wind gusts expected?",
    "Is the wind dangerous for my boat?",
    "Will wind speed increase?",
    "What are the current wind conditions?",
    "Is there a high wind warning?"
],

"temperature": [
    "What is the current temperature?",
    "How hot is it?",
    "What is the temperature near me?",
    "Tell me the current air temperature.",
    "Will the temperature increase?",
    "Will the temperature decrease?",
    "What temperature is expected today?",
    "Is the temperature dangerous?",
    "Is it very hot today?",
    "What is the temperature at sea?"
],

"humidity": [
    "What is the current humidity?",
    "How humid is it?",
    "Tell me the humidity level.",
    "Is humidity high?",
    "Is the humidity dangerous?",
    "What is the humidity near my boat?"
],

"pressure": [
    "What is the current air pressure?",
    "Tell me the atmospheric pressure.",
    "Is the air pressure changing?",
    "Is the pressure low?",
    "What is the pressure near me?"
],

"cloud": [
    "How cloudy is it?",
    "What is the cloud cover?",
    "Are there many clouds?",
    "Is the sky cloudy?",
    "Will cloud cover increase?"
],

"storm": [
    "Is there a storm near me?",
    "Is a storm approaching?",
    "Is there a storm warning?",
    "Will a storm affect my boat?",
    "Are storm conditions expected?",
    "Is there severe weather near me?"
],

"cyclone": [
    "Is there a cyclone near me?",
    "Is a cyclone approaching?",
    "Is there a cyclone warning?",
    "Will the cyclone affect my area?",
    "Will the cyclone affect fishing?",
    "Should I return to shore because of the cyclone?",
    "Where is the cyclone?",
    "What is the cyclone status?",
    "How dangerous is the cyclone?",
    "When will the cyclone reach my area?"
],

"lightning": [
    "Is there a lightning risk?",
    "Is lightning expected?",
    "Is there a thunderstorm nearby?",
    "Can lightning affect my boat?",
    "Should I stay at sea during lightning?",
    "Is there a lightning warning?"
],

# ------------------------------------------------------------
# OCEAN / SEA
# ------------------------------------------------------------

"sea_condition": [
    "How is the sea right now?",
    "What are the current sea conditions?",
    "How is the ocean near me?",
    "Is the sea calm?",
    "Is the sea rough?",
    "Are sea conditions dangerous?",
    "What is the current ocean condition?",
    "Can my boat handle the sea conditions?",
    "Is the sea safe for fishing?",
    "What is the marine condition?"
],

"wave_height": [
    "What is the current wave height?",
    "How high are the waves?",
    "Are the waves high?",
    "Are there dangerous waves?",
    "What wave height is expected?",
    "Will wave height increase?",
    "Will waves affect my boat?",
    "How rough are the waves?",
    "Tell me the wave conditions.",
    "What are the current wave heights?"
],

"swell": [
    "What is the current swell?",
    "What is the swell height?",
    "What direction is the swell coming from?",
    "Is there a large swell?",
    "Will swell increase?",
    "Is the swell dangerous for my boat?"
],

"sea_state": [
    "What is the current sea state?",
    "Is the sea state safe?",
    "What is the sea state near me?",
    "Is the sea state rough?",
    "What sea state should I expect?",
    "Will the sea state become dangerous?"
],

"tide": [
    "What is the current tide?",
    "Is the tide rising or falling?",
    "When is the next high tide?",
    "When is the next low tide?",
    "What time is high tide?",
    "What time is low tide?",
    "What is the tide forecast?",
    "Will the tide affect my boat?",
    "Is the tide dangerous?",
    "Tell me today's tide."
],

"sea_temperature": [
    "What is the sea water temperature?",
    "What is the current sea surface temperature?",
    "What is the SST?",
    "Tell me the ocean temperature.",
    "Is the sea temperature high?",
    "What is the water temperature near me?"
],

"ocean_current": [
    "What is the current ocean current?",
    "What is the sea current near me?",
    "Which direction is the current flowing?",
    "Is the current strong?",
    "Will the current affect my boat?",
    "Is the ocean current dangerous?"
],

"visibility": [
    "How is visibility at sea?",
    "What is the current visibility?",
    "Is visibility poor?",
    "Is fog affecting visibility?",
    "Can I safely travel with this visibility?",
    "Will visibility improve?"
],

# ------------------------------------------------------------
# FISHERIES
# ------------------------------------------------------------

"pfz": [
    "Where is the nearest PFZ?",
    "Where is the nearest Potential Fishing Zone?",
    "Find the closest fishing zone.",
    "Show me the nearest fishing area.",
    "Where should I go fishing?",
    "Which PFZ is closest to me?",
    "Find a good fishing zone.",
    "Show potential fishing zones.",
    "Where is the PFZ advisory?",
    "Give me the nearest PFZ."
],

"fishing_distance": [
    "How far is the nearest fishing zone?",
    "What is the distance to the PFZ?",
    "How far do I need to travel to the fishing zone?",
    "Tell me the PFZ distance.",
    "How many kilometers is the fishing zone away?",
    "How far is the nearest PFZ?"
],

"fishing_direction": [
    "Which direction should I go for fishing?",
    "Which direction is the PFZ?",
    "Give me the direction to the fishing zone.",
    "What bearing should I take?",
    "Which way should my boat travel?",
    "How do I reach the nearest PFZ?"
],

"fishing_depth": [
    "What is the depth of the fishing zone?",
    "How deep is the PFZ?",
    "Tell me the fishing zone depth.",
    "What is the water depth there?",
    "How deep is the sea at the PFZ?"
],

"fishing_productivity": [
    "Is this a good fishing area?",
    "Is fishing likely to be productive here?",
    "Can I expect a good catch?",
    "Which area is productive for fishing?",
    "Where are fish likely to be found?",
    "Is this area suitable for fishing?",
    "Which area has better fishing potential?"
],

"sst_fishing": [
    "What is the SST in the fishing area?",
    "What is the sea surface temperature at the PFZ?",
    "Tell me the SST near the fishing zone.",
    "How warm is the water in the fishing area?"
],

"chlorophyll": [
    "What is the chlorophyll level?",
    "What is the chlorophyll concentration?",
    "Tell me the chlorophyll value.",
    "Is chlorophyll high in the fishing area?",
    "What is the chlorophyll level near the PFZ?"
],

"fishing_advisory": [
    "Are there fishing advisories?",
    "Is there a fishing advisory for my area?",
    "What are the latest fishing advisories?",
    "Are there any restrictions on fishing?",
    "Tell me the fishing advisory.",
    "Is there an INCOIS fishing advisory?"
],

# ------------------------------------------------------------
# VESSEL / AIS
# ------------------------------------------------------------

"nearby_vessels": [
    "Are there vessels near me?",
    "Are there boats near my boat?",
    "Show nearby vessels.",
    "Are there ships near my location?",
    "What vessels are around me?",
    "Are there any boats nearby?",
    "Show ships near my location.",
    "Tell me about nearby vessels."
],

"nearest_vessel": [
    "Where is the nearest vessel?",
    "Which vessel is closest to me?",
    "Find the closest ship.",
    "Where is the closest boat?",
    "Tell me about the nearest vessel.",
    "Which ship is nearest to my boat?"
],

"vessel_count": [
    "How many vessels are near me?",
    "How many boats are nearby?",
    "How many ships are around me?",
    "Count the nearby vessels.",
    "How many AIS vessels are nearby?"
],

"vessel_distance": [
    "How far is the nearest vessel?",
    "What is the distance to the nearest ship?",
    "How far away is the closest boat?",
    "Tell me the nearest vessel distance."
],

"ais": [
    "What is AIS?",
    "Show AIS vessels near me.",
    "What AIS vessels are nearby?",
    "Show AIS traffic.",
    "Give me AIS information.",
    "Where are AIS vessels?"
],

"vessel_traffic": [
    "Is vessel traffic high?",
    "Is there heavy ship traffic?",
    "How busy is the vessel traffic?",
    "Are many ships nearby?",
    "Is marine traffic high?"
],

"collision_risk": [
    "Is there a collision risk?",
    "Is any vessel dangerously close?",
    "Could my boat collide with another vessel?",
    "Is a ship approaching my boat?",
    "Is there a dangerous vessel nearby?",
    "Warn me about nearby vessels."
],

# ------------------------------------------------------------
# GIS / LOCATION
# ------------------------------------------------------------

"my_location": [
    "Where am I?",
    "Where is my boat?",
    "Show my current location.",
    "What are my coordinates?",
    "Show my location on the marine map.",
    "Where is my current position?",
    "Tell me my latitude and longitude."
],

"marine_area": [
    "Which marine area am I in?",
    "What marine zone am I in?",
    "Identify my marine area.",
    "Tell me the name of this marine area.",
    "What sea region am I currently in?"
],

"eez": [
    "Am I inside the Indian EEZ?",
    "Am I within India's EEZ?",
    "Check my EEZ status.",
    "Does my location fall inside the EEZ?",
    "How close am I to the EEZ boundary?",
    "Where is the Indian EEZ?"
],

"protected_area": [
    "Am I inside a protected marine area?",
    "Is this a marine protected area?",
    "Am I in a protected zone?",
    "Check protected area status.",
    "Can I fish inside this protected area?",
    "Is this area environmentally protected?"
],

"restricted_area": [
    "Am I inside a restricted area?",
    "Is this a restricted marine zone?",
    "Can I enter this area?",
    "Is fishing allowed here?",
    "Check restricted area status.",
    "Is this area restricted?"
],

"boundary": [
    "Where is the nearest marine boundary?",
    "How close am I to the marine boundary?",
    "Show the nearest boundary.",
    "Where is the maritime boundary?",
    "Am I close to an international boundary?"
],

"geofence": [
    "Am I crossing a geofence?",
    "Did I enter a geofenced area?",
    "Is a geofence warning active?",
    "Check my geofence status.",
    "Have I crossed a restricted boundary?"
],

"fishing_allowed": [
    "Is fishing allowed here?",
    "Can I fish in this area?",
    "Am I allowed to fish here?",
    "Is fishing permitted at my location?",
    "Can fishermen operate in this zone?"
],

# ------------------------------------------------------------
# SAFETY
# ------------------------------------------------------------

"fishing_safety": [
    "Is it safe to go fishing today?",
    "Should I go fishing now?",
    "Is today suitable for fishing?",
    "Is fishing safe right now?",
    "Can I safely go fishing?",
    "Should I avoid fishing today?",
    "Is the sea safe for fishing?"
],

"boat_safety": [
    "Is it safe for my boat to go to sea?",
    "Can my boat go to sea now?",
    "Is it safe to leave shore?",
    "Should I take my boat into the sea?",
    "Is my boat safe in the current conditions?",
    "Can I safely travel at sea?"
],

"return_shore": [
    "Should I return to shore?",
    "Should I go back to shore?",
    "Is it safer to return?",
    "Should I stop fishing and return?",
    "Should my boat return because of weather?",
    "Do I need to return to shore?"
],

"precautions": [
    "What precautions should I take before going to sea?",
    "What safety checks should I do before fishing?",
    "What should I carry before going to sea?",
    "Give me marine safety precautions.",
    "What should fishermen check before leaving shore?",
    "What safety equipment should I carry?"
],

"marine_risk": [
    "What is the current marine risk?",
    "What is my overall marine risk?",
    "Is there any danger near me?",
    "How dangerous are the current conditions?",
    "Give me the marine safety status.",
    "What hazards are near my boat?"
],

# ------------------------------------------------------------
# NAVIGATION / ROUTE
# ------------------------------------------------------------

"safe_route": [
    "Which route is safest for my boat?",
    "Find a safe route.",
    "Suggest the safest route.",
    "What route should my boat take?",
    "Give me a safe marine route.",
    "Which path should I use?",
    "Find the safest way to my destination."
],

"route_hazard": [
    "Are there hazards on my route?",
    "Check my route for hazards.",
    "What dangers are ahead?",
    "Are there dangerous areas along my route?",
    "Is my planned route safe?",
    "What hazards are on the way?"
],

"route_weather": [
    "Is the weather safe along my route?",
    "Will bad weather affect my route?",
    "What weather will I face on my route?",
    "Check weather along my route.",
    "Are there strong winds along my route?"
],

"route_restricted": [
    "Does my route pass through a restricted area?",
    "Will my route enter a restricted zone?",
    "Check my route against restricted areas.",
    "Does my route cross a protected area?",
    "Will I cross a maritime boundary?"
],

# ------------------------------------------------------------
# SOS / EMERGENCY
# ------------------------------------------------------------

"sos_activate": [
    "How do I activate SOS?",
    "How can I send an SOS?",
    "I need to activate SOS.",
    "Where is the SOS button?",
    "How do I send an emergency alert?",
    "I need emergency assistance."
],

"sos_status": [
    "Is my SOS active?",
    "Check my SOS status.",
    "Has my SOS been activated?",
    "Is my emergency alert active?",
    "What is the status of my SOS?"
],

"sos_location": [
    "Send my current location with SOS.",
    "Share my GPS location.",
    "Send my location to rescue.",
    "Can I send my current coordinates?",
    "How do I share my emergency location?"
],

"emergency": [
    "I am in an emergency.",
    "I need help at sea.",
    "There is an emergency on my boat.",
    "I need emergency assistance.",
    "Help me, I am in danger.",
    "What should I do in an emergency?"
],

"engine_failure": [
    "My boat engine has failed.",
    "My engine stopped working.",
    "My boat engine is not working.",
    "What should I do if my engine fails?",
    "My boat has an engine problem.",
    "I am stranded because my engine failed."
],

"sinking": [
    "My boat is sinking.",
    "My boat is taking water.",
    "My boat may sink.",
    "Water is entering my boat.",
    "I am sinking.",
    "Help, my boat is sinking."
],

"man_overboard": [
    "Someone has fallen overboard.",
    "A person fell into the sea.",
    "Someone is in the water.",
    "A fisherman has fallen overboard.",
    "What should I do for a man overboard emergency?"
],

"medical": [
    "There is a medical emergency on my boat.",
    "Someone on my boat needs medical help.",
    "I need medical assistance at sea.",
    "Someone is seriously injured.",
    "There is a health emergency on my boat."
],

"boat_damage": [
    "My boat is damaged.",
    "My boat has a serious problem.",
    "The boat hull is damaged.",
    "My boat has been damaged at sea.",
    "What should I do if my boat is damaged?"
],

"lost_at_sea": [
    "I am lost at sea.",
    "I don't know where my boat is.",
    "I am unable to find my way back.",
    "I am stranded at sea.",
    "I have lost my route.",
    "Help me find my location."
],

# ------------------------------------------------------------
# GENERAL ORCA
# ------------------------------------------------------------

"orca": [
    "What is Ask ORCA?",
    "What can ORCA do?",
    "How can ORCA help me?",
    "What information can I get from ORCA?",
    "What can I ask ORCA?",
    "How does ORCA work?",
    "Tell me about ORCA.",
    "What services does ORCA provide?",
    "Can ORCA help fishermen?",
    "Can ORCA help me during an emergency?"
],

"pfz_info": [
    "What is PFZ?",
    "What does PFZ mean?",
    "Explain Potential Fishing Zone.",
    "What is a Potential Fishing Zone?",
    "How does PFZ help fishermen?"
],

"ais_info": [
    "What is AIS?",
    "What does AIS mean?",
    "Explain AIS.",
    "How does AIS work?",
    "Why is AIS useful for boats?"
],

"eez_info": [
    "What is EEZ?",
    "What does EEZ mean?",
    "Explain the Indian EEZ.",
    "Why is EEZ important?",
    "What is an Exclusive Economic Zone?"
],

"marine_safety_info": [
    "How can I stay safe at sea?",
    "What are basic marine safety rules?",
    "Give me fishing safety tips.",
    "How can fishermen stay safe?",
    "What should I do before going offshore?"
],

# ------------------------------------------------------------
# FALLBACK / UNKNOWN
# ------------------------------------------------------------

"general_marine": [
    "Tell me about the sea.",
    "Tell me about the ocean.",
    "Give me marine information.",
    "I need information about the sea.",
    "I need ocean information.",
    "Tell me something about marine conditions."
]

}


# ============================================================
# AGENT MAPPING
# ============================================================

AGENTS = {

"weather_current": "weather",
"weather_forecast": "weather",
"rain": "weather",
"wind": "weather",
"temperature": "weather",
"humidity": "weather",
"pressure": "weather",
"cloud": "weather",
"storm": "weather",
"cyclone": "weather",
"lightning": "weather",

"sea_condition": "ocean",
"wave_height": "ocean",
"swell": "ocean",
"sea_state": "ocean",
"tide": "ocean",
"sea_temperature": "ocean",
"ocean_current": "ocean",
"visibility": "ocean",

"pfz": "fisheries",
"fishing_distance": "fisheries",
"fishing_direction": "fisheries",
"fishing_depth": "fisheries",
"fishing_productivity": "fisheries",
"sst_fishing": "fisheries",
"chlorophyll": "fisheries",
"fishing_advisory": "fisheries",

"nearby_vessels": "vessel",
"nearest_vessel": "vessel",
"vessel_count": "vessel",
"vessel_distance": "vessel",
"ais": "vessel",
"vessel_traffic": "vessel",
"collision_risk": "vessel",

"my_location": "gis",
"marine_area": "gis",
"eez": "gis",
"protected_area": "gis",
"restricted_area": "gis",
"boundary": "gis",
"geofence": "gis",
"fishing_allowed": "gis",

"fishing_safety": "safety",
"boat_safety": "safety",
"return_shore": "safety",
"precautions": "safety",
"marine_risk": "safety",

"safe_route": "navigation",
"route_hazard": "navigation",
"route_weather": "navigation",
"route_restricted": "navigation",

"sos_activate": "sos",
"sos_status": "sos",
"sos_location": "sos",
"emergency": "sos",
"engine_failure": "sos",
"sinking": "sos",
"man_overboard": "sos",
"medical": "sos",
"boat_damage": "sos",
"lost_at_sea": "sos",

"orca": "general",
"pfz_info": "general",
"ais_info": "general",
"eez_info": "general",
"marine_safety_info": "general",
"general_marine": "general"
}


# ============================================================
# TRANSLATION
# ============================================================

def translate(text, target):
    if target == "en":
        return text

    try:
        return GoogleTranslator(
            source="en",
            target=target
        ).translate(text)

    except Exception as e:
        print("Translation error:", target, e)
        return text


# ============================================================
# GENERATE DATASET
# ============================================================

dataset = []

counter = 1

print("\nGenerating Ask ORCA multilingual dataset...\n")

for intent, questions in QUESTIONS.items():

    agent = AGENTS.get(intent, "general")

    for english_question in questions:

        translations = {}

        for lang, lang_code in LANGUAGES.items():

            print(
                f"[{counter}] "
                f"{intent} -> {lang}"
            )

            translations[lang] = translate(
                english_question,
                lang_code
            )

            time.sleep(0.15)

        dataset.append({
            "id": f"ORCA-{counter:05d}",
            "intent": intent,
            "agent": agent,
            "priority": (
                10 if agent == "sos"
                else 9 if agent in ["safety", "navigation"]
                else 8
            ),
            "questions": translations
        })

        counter += 1


# ============================================================
# SAVE DATASET
# ============================================================

output = {
    "dataset_name": "Ask ORCA Multilingual Marine Question Dataset",
    "version": "1.0",
    "languages": list(LANGUAGES.keys()),
    "language_names": {
        "en": "English",
        "hi": "Hindi",
        "mr": "Marathi",
        "gu": "Gujarati",
        "bn": "Bengali",
        "ta": "Tamil",
        "te": "Telugu",
        "kn": "Kannada",
        "ml": "Malayalam",
        "or": "Odia",
        "pa": "Punjabi"
    },

    "description":
        "Multilingual question-intent dataset for Ask ORCA. "
        "Questions are routed to ORCA agents. "
        "Live answers must come from agents or approved official sources.",

    "priority_order": [
        "question_dataset",
        "orca_agent",
        "government_live_data",
        "online_fallback"
    ],

    "records": dataset
}


with open(
    "orca_questions.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        output,
        f,
        ensure_ascii=False,
        indent=2
    )


print("\n========================================")
print("DATASET CREATED SUCCESSFULLY")
print("========================================")
print("Questions:", len(dataset))
print("Languages:", len(LANGUAGES))
print(
    "Language-question pairs:",
    len(dataset) * len(LANGUAGES)
)
print("File: orca_questions.json")
print("========================================")
