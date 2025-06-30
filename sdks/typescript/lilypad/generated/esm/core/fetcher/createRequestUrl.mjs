import qs from "qs";
export function createRequestUrl(baseUrl, queryParameters) {
    return Object.keys(queryParameters !== null && queryParameters !== void 0 ? queryParameters : {}).length > 0
        ? `${baseUrl}?${qs.stringify(queryParameters, { arrayFormat: "repeat" })}`
        : baseUrl;
}
