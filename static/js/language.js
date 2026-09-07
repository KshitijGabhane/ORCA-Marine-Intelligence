// ============================================================
// ORCA MULTILINGUAL FRONTEND
// ============================================================

const ORCA_LANGUAGE_KEY = "orcaLanguage";

const ORCA_SUPPORTED_LANGUAGES = {
    en: "English",
    hi: "हिंदी",
    mr: "मराठी",
    gu: "ગુજરાતી",
    bn: "বাংলা",
    ta: "தமிழ்",
    te: "తెలుగు",
    kn: "ಕನ್ನಡ",
    ml: "മലയാളം",
    or: "ଓଡ଼ିଆ",
    pa: "ਪੰਜਾਬੀ"
};


// ============================================================
// LOAD TRANSLATION FILE
// ============================================================

async function loadLanguage(language) {

    try {

        const response = await fetch(
            `/static/translations/${language}.json`
        );

        if (!response.ok) {
            throw new Error("Translation file not found");
        }

        const translations = await response.json();

        applyTranslations(translations);

        localStorage.setItem(
            ORCA_LANGUAGE_KEY,
            language
        );

        document.documentElement.lang = language;

        console.log(
            "ORCA language changed to:",
            language
        );

    } catch (error) {

        console.error(
            "Language loading error:",
            error
        );

    }
}


// ============================================================
// APPLY TRANSLATIONS
// ============================================================

function applyTranslations(translations) {

    /*
       Translate elements using:

       data-i18n="key"
    */

    document
        .querySelectorAll("[data-i18n]")
        .forEach(element => {

            const key = element.dataset.i18n;

            if (translations[key] !== undefined) {

                element.textContent =
                    translations[key];

            }

        });


    /*
       Translate placeholders using:

       data-i18n-placeholder="key"
    */

    document
        .querySelectorAll("[data-i18n-placeholder]")
        .forEach(element => {

            const key =
                element.dataset.i18nPlaceholder;

            if (translations[key] !== undefined) {

                element.placeholder =
                    translations[key];

            }

        });


    /*
       Translate buttons/options etc.
    */

    document
        .querySelectorAll("[data-i18n-html]")
        .forEach(element => {

            const key = element.dataset.i18nHtml;

            if (translations[key] !== undefined) {

                element.innerHTML =
                    translations[key];

            }

        });
}


// ============================================================
// LANGUAGE SELECTOR
// ============================================================

function createLanguageSelector() {

    /*
       Don't create duplicate selector
    */

    if (document.getElementById("orcaLanguageSelector")) {
        return;
    }


    const selector =
        document.createElement("select");

    selector.id =
        "orcaLanguageSelector";

    selector.className =
        "orca-language-selector";


    /*
       Create options
    */

    Object.entries(
        ORCA_SUPPORTED_LANGUAGES
    ).forEach(([code, name]) => {

        const option =
            document.createElement("option");

        option.value = code;

        option.textContent = name;

        selector.appendChild(option);

    });


    /*
       Previously selected language
    */

    const savedLanguage =
        localStorage.getItem(
            ORCA_LANGUAGE_KEY
        ) || "en";


    selector.value =
        savedLanguage;


    /*
       Change language
    */

    selector.addEventListener(
        "change",
        function () {

            loadLanguage(this.value);

        }
    );


    /*
       Put selector inside top-right
    */

    const topRight =
        document.querySelector(
            ".top-right"
        );


    if (topRight) {

        topRight.insertBefore(
            selector,
            topRight.firstChild
        );

    }

}


// ============================================================
// INITIALIZE LANGUAGE SYSTEM
// ============================================================

function initializeLanguage() {

    createLanguageSelector();


    const savedLanguage =
        localStorage.getItem(
            ORCA_LANGUAGE_KEY
        ) || "en";


    loadLanguage(savedLanguage);

}


// ============================================================
// START
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    initializeLanguage
);