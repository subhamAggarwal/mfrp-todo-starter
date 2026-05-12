const JSDOMEnvironmentModule = require('jest-environment-jsdom').default || require('jest-environment-jsdom');

class JSDOMEnvironmentWithFetch extends JSDOMEnvironmentModule {
  constructor(config, options) {
    super(config, options);
    this.global.fetch = fetch;
    this.global.Request = Request;
    this.global.Response = Response;
    this.global.Headers = Headers;
    const { TextEncoder, TextDecoder } = require('util');
    this.global.TextEncoder = TextEncoder;
    this.global.TextDecoder = TextDecoder;
    if (typeof this.global.BroadcastChannel === 'undefined') {
      this.global.BroadcastChannel = class BroadcastChannel {
        constructor(name) { this.name = name; }
        postMessage() {}
        close() {}
        addEventListener() {}
        removeEventListener() {}
      };
    }
    if (typeof this.global.AbortController === 'undefined') {
      this.global.AbortController = AbortController;
      this.global.AbortSignal = AbortSignal;
    }
    if (typeof this.global.matchMedia === 'undefined') {
      this.global.matchMedia = () => ({
        matches: false,
        media: '',
        onchange: null,
        addListener() {},
        removeListener() {},
        addEventListener() {},
        removeEventListener() {},
        dispatchEvent() { return true; },
      });
    }
    const { WritableStream, ReadableStream, TransformStream } = require('node:stream/web');
    if (typeof this.global.WritableStream === 'undefined') {
      this.global.WritableStream = WritableStream;
      this.global.ReadableStream = ReadableStream;
      this.global.TransformStream = TransformStream;
    }
  }
}

module.exports = JSDOMEnvironmentWithFetch;
