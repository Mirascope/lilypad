import https from 'https';
import http, { OutgoingHttpHeaders } from 'http';
import { URL } from 'url';

export interface HttpRequestOptions {
  url: string;
  method?: string;
  headers?: Record<string, string>;
  body?: string | Buffer;
  timeout?: number;
}

export interface HttpResponse {
  statusCode: number;
  headers: http.IncomingHttpHeaders;
  body: string;
}

export async function request(options: HttpRequestOptions): Promise<HttpResponse> {
  const url = new URL(options.url);
  const isHttps = url.protocol === 'https:';
  const lib = isHttps ? https : http;

  const headers: OutgoingHttpHeaders = {
    ...options.headers,
    // Important headers should not be overridden
    'Content-Type': 'application/json',
  };

  if (options.body && typeof options.body === 'string') {
    headers['Content-Length'] = String(Buffer.byteLength(options.body));
  }

  const requestOptions: https.RequestOptions = {
    hostname: url.hostname,
    port: url.port || (isHttps ? 443 : 80),
    path: url.pathname + url.search,
    method: options.method || 'GET',
    headers,
    timeout: options.timeout || 30000,
  };

  return new Promise((resolve, reject) => {
    const req = lib.request(requestOptions, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        resolve({
          statusCode: res.statusCode || 0,
          headers: res.headers,
          body: data,
        });
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    if (options.body) {
      req.write(options.body);
    }

    req.end();
  });
}
