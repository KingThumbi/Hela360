export interface CountryOption {
  code: string;
  name: string;
}

const ISO_ALPHA_2_CODES = `
AD AE AF AG AI AL AM AO AQ AR AS AT AU AW AX AZ
BA BB BD BE BF BG BH BI BJ BL BM BN BO BQ BR BS BT BV BW BY BZ
CA CC CD CF CG CH CI CK CL CM CN CO CR CU CV CW CX CY CZ
DE DJ DK DM DO DZ
EC EE EG EH ER ES ET
FI FJ FK FM FO FR
GA GB GD GE GF GG GH GI GL GM GN GP GQ GR GS GT GU GW GY
HK HM HN HR HT HU
ID IE IL IM IN IO IQ IR IS IT
JE JM JO JP
KE KG KH KI KM KN KP KR KW KY KZ
LA LB LC LI LK LR LS LT LU LV LY
MA MC MD ME MF MG MH MK ML MM MN MO MP MQ MR MS MT MU MV MW MX MY MZ
NA NC NE NF NG NI NL NO NP NR NU NZ
OM
PA PE PF PG PH PK PL PM PN PR PS PT PW PY
QA
RE RO RS RU RW
SA SB SC SD SE SG SH SI SJ SK SL SM SN SO SR SS ST SV SX SY SZ
TC TD TF TG TH TJ TK TL TM TN TO TR TT TV TW TZ
UA UG UM US UY UZ
VA VC VE VG VI VN VU
WF WS
YE YT ZA ZM ZW
`
  .trim()
  .split(/\s+/);

const regionNames =
  typeof Intl !== "undefined" &&
  typeof Intl.DisplayNames !== "undefined"
    ? new Intl.DisplayNames(["en"], {
        type: "region",
      })
    : null;

export const COUNTRIES: CountryOption[] =
  ISO_ALPHA_2_CODES
    .map((code) => ({
      code,
      name:
        regionNames?.of(code) ??
        code,
    }))
    .sort((left, right) =>
      left.name.localeCompare(
        right.name,
        "en",
        {
          sensitivity: "base",
        },
      ),
    );

const COUNTRY_BY_NAME = new Map(
  COUNTRIES.map((country) => [
    country.name.toLocaleLowerCase("en"),
    country,
  ]),
);

const COUNTRY_BY_CODE = new Map(
  COUNTRIES.map((country) => [
    country.code,
    country,
  ]),
);

const COUNTRY_ALIASES = new Map<
  string,
  string
>([
  ["uae", "AE"],
  ["u.a.e.", "AE"],
  ["united arab emirates", "AE"],

  ["uk", "GB"],
  ["u.k.", "GB"],
  ["great britain", "GB"],
  ["britain", "GB"],
  ["united kingdom", "GB"],

  ["usa", "US"],
  ["u.s.a.", "US"],
  ["us", "US"],
  ["u.s.", "US"],
  ["united states of america", "US"],
  ["united states", "US"],

  ["south korea", "KR"],
  ["republic of korea", "KR"],

  ["north korea", "KP"],
  ["democratic people's republic of korea", "KP"],

  ["russia", "RU"],
  ["russian federation", "RU"],

  ["tanzania", "TZ"],
  ["united republic of tanzania", "TZ"],

  ["vatican", "VA"],
  ["vatican city", "VA"],
]);

export function countryByCode(
  code: string | null | undefined,
): CountryOption | null {
  if (!code) {
    return null;
  }

  return (
    COUNTRY_BY_CODE.get(
      code.trim().toUpperCase(),
    ) ?? null
  );
}

export function canonicalCountryName(
  value: string | null | undefined,
): string {
  if (!value) {
    return "";
  }

  const normalized = value.trim();

  if (!normalized) {
    return "";
  }

  const codeMatch =
    countryByCode(normalized);

  if (codeMatch) {
    return codeMatch.name;
  }

  const nameMatch =
    COUNTRY_BY_NAME.get(
      normalized.toLocaleLowerCase("en"),
    );

  if (nameMatch) {
    return nameMatch.name;
  }

  const aliasCode =
    COUNTRY_ALIASES.get(
      normalized.toLocaleLowerCase("en"),
    );

  if (aliasCode) {
    return (
      COUNTRY_BY_CODE.get(aliasCode)
        ?.name ?? normalized
    );
  }

  /*
   * Preserve unknown legacy values instead of
   * silently discarding them. The selector can
   * surface them for review.
   */
  return normalized;
}

export function isCanonicalCountry(
  value: string | null | undefined,
): boolean {
  if (!value) {
    return false;
  }

  return COUNTRY_BY_NAME.has(
    value
      .trim()
      .toLocaleLowerCase("en"),
  );
}
