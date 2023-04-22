class BiliAPI {
    #url;
    #key;
    constructor(proxy_url, key, uid) {
        const cookie = window.document.cookie;
        this.#url = proxy_url
        this.#key = key ?? null
        this.uid = uid ?? (cookie ? Number(cookie.match(/DedeUserID=(\w+)/)[1]) : null);
    }

    setProxyKey(key){
        this.#key = key
    }

    pfetch(input, init){
        init.url = input
        init._key = this.#key
        init._uid = this.uid
        return fetch(this.#url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(init),
        })
    }
}


class BVParser {
    constructor() {
        const table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF';
        const tr = function () {
            let tr = {};
            for (let i = 0; i < 58; ++i) {
                tr[table[i]] = i;
            }
            return tr;
        } ();
        const s = [11, 10, 3, 8, 4, 6];
        const xor = 177451812;
        const add = 8728348608;
        this.dec = (x) => {
            let r = 0;
            for (let i = 0; i < 6; ++i) {
                r += tr[x[s[i]]] * 58 ** i;
            }
            return (r - add) ^ xor;
        };
        this.enc = (x) => {
            x = (x ^ xor) + add;
            let r = Array.from('BV1  4 1 7  ');
            for (let i = 0; i < 6; ++i) {
                r[s[i]] = table[Math.floor(x / 58 ** i) % 58];
            }
            return r.join("");
        };
    }
    isBV(x){
        return !!x?.match(/[bB][vV][fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF]{10}/);
    }
    isAv(x){
        return !!x?.match(/av(\d{1,8})/)
    }
}