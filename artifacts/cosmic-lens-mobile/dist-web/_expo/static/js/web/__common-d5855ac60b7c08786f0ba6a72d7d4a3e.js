__d(function(g,r,_i,a,m,_e,d){"use strict";Object.defineProperty(_e,'__esModule',{value:!0}),Object.defineProperty(_e,"FirebaseError",{enumerable:!0,get:function(){return n.FirebaseError}}),Object.defineProperty(_e,"SDK_VERSION",{enumerable:!0,get:function(){return ie}}),Object.defineProperty(_e,"_DEFAULT_ENTRY_NAME",{enumerable:!0,get:function(){return H}}),Object.defineProperty(_e,"_addComponent",{enumerable:!0,get:function(){return V}}),Object.defineProperty(_e,"_addOrOverwriteComponent",{enumerable:!0,get:function(){return W}}),Object.defineProperty(_e,"_apps",{enumerable:!0,get:function(){return L}}),Object.defineProperty(_e,"_clearComponents",{enumerable:!0,get:function(){return Z}}),Object.defineProperty(_e,"_components",{enumerable:!0,get:function(){return J}}),Object.defineProperty(_e,"_getProvider",{enumerable:!0,get:function(){return K}}),Object.defineProperty(_e,"_isFirebaseApp",{enumerable:!0,get:function(){return G}}),Object.defineProperty(_e,"_isFirebaseServerApp",{enumerable:!0,get:function(){return X}}),Object.defineProperty(_e,"_isFirebaseServerAppSettings",{enumerable:!0,get:function(){return Q}}),Object.defineProperty(_e,"_registerComponent",{enumerable:!0,get:function(){return q}}),Object.defineProperty(_e,"_removeServiceInstance",{enumerable:!0,get:function(){return Y}}),Object.defineProperty(_e,"_serverApps",{enumerable:!0,get:function(){return U}}),Object.defineProperty(_e,"deleteApp",{enumerable:!0,get:function(){return fe}}),Object.defineProperty(_e,"getApp",{enumerable:!0,get:function(){return ce}}),Object.defineProperty(_e,"getApps",{enumerable:!0,get:function(){return pe}}),Object.defineProperty(_e,"initializeApp",{enumerable:!0,get:function(){return oe}}),Object.defineProperty(_e,"initializeServerApp",{enumerable:!0,get:function(){return se}}),Object.defineProperty(_e,"onLog",{enumerable:!0,get:function(){return he}}),Object.defineProperty(_e,"registerVersion",{enumerable:!0,get:function(){return le}}),Object.defineProperty(_e,"setLogLevel",{enumerable:!0,get:function(){return ue}});var e=r(d[0]),t=r(d[1]),n=r(d[2]),i=r(d[3]);
/**
   * @license
   * Copyright 2019 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */
class o{constructor(e){this.container=e}getPlatformInfoString(){return this.container.getProviders().map(e=>{if(s(e)){const t=e.getImmediate();return`${t.library}/${t.version}`}return null}).filter(e=>e).join(' ')}}function s(e){const t=e.getComponent();return"VERSION"===t?.type}const c="@firebase/app",p="0.14.11",f=new t.Logger('@firebase/app'),l="@firebase/app-compat",h="@firebase/analytics-compat",u="@firebase/analytics",b="@firebase/app-check-compat",v="@firebase/app-check",C="@firebase/auth",_="@firebase/auth-compat",y="@firebase/database",w="@firebase/data-connect",D="@firebase/database-compat",O="@firebase/functions",E="@firebase/functions-compat",P="@firebase/installations",S="@firebase/installations-compat",j="@firebase/messaging",A="@firebase/messaging-compat",I="@firebase/performance",k="@firebase/performance-compat",F="@firebase/remote-config",$="@firebase/remote-config-compat",N="@firebase/storage",x="@firebase/storage-compat",R="@firebase/firestore",T="@firebase/ai",B="@firebase/firestore-compat",z="firebase",H='[DEFAULT]',M={[c]:'fire-core',[l]:'fire-core-compat',[u]:'fire-analytics',[h]:'fire-analytics-compat',[v]:'fire-app-check',[b]:'fire-app-check-compat',[C]:'fire-auth',[_]:'fire-auth-compat',[y]:'fire-rtdb',[w]:'fire-data-connect',[D]:'fire-rtdb-compat',[O]:'fire-fn',[E]:'fire-fn-compat',[P]:'fire-iid',[S]:'fire-iid-compat',[j]:'fire-fcm',[A]:'fire-fcm-compat',[I]:'fire-perf',[k]:'fire-perf-compat',[F]:'fire-rc',[$]:'fire-rc-compat',[N]:'fire-gcs',[x]:'fire-gcs-compat',[R]:'fire-fst',[B]:'fire-fst-compat',[T]:'fire-vertex','fire-js':'fire-js',[z]:'fire-js-all'},L=new Map,U=new Map,J=new Map;function V(e,t){try{e.container.addComponent(t)}catch(n){f.debug(`Component ${t.name} failed to register with FirebaseApp ${e.name}`,n)}}function W(e,t){e.container.addOrOverwriteComponent(t)}function q(e){const t=e.name;if(J.has(t))return f.debug(`There were multiple attempts to register component ${t}.`),!1;J.set(t,e);for(const t of L.values())V(t,e);for(const t of U.values())V(t,e);return!0}function K(e,t){const n=e.container.getProvider('heartbeat').getImmediate({optional:!0});return n&&n.triggerHeartbeat(),e.container.getProvider(t)}function Y(e,t,n=H){K(e,t).clearInstance(n)}function G(e){return void 0!==e.options}function Q(e){return!G(e)&&('authIdToken'in e||'appCheckToken'in e||'releaseOnDeref'in e||'automaticDataCollectionEnabled'in e)}function X(e){return null!=e&&void 0!==e.settings}function Z(){J.clear()}
/**
   * @license
   * Copyright 2019 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */const ee={"no-app":"No Firebase App '{$appName}' has been created - call initializeApp() first","bad-app-name":"Illegal App name: '{$appName}'","duplicate-app":"Firebase App named '{$appName}' already exists with different options or config","app-deleted":"Firebase App named '{$appName}' already deleted","server-app-deleted":'Firebase Server App has been deleted',"no-options":'Need to provide options, when not being deployed to hosting via source.',"invalid-app-argument":"firebase.{$appName}() takes either no argument or a Firebase App instance.","invalid-log-argument":'First argument to `onLog` must be null or a function.',"idb-open":'Error thrown when opening IndexedDB. Original error: {$originalErrorMessage}.',"idb-get":'Error thrown when reading from IndexedDB. Original error: {$originalErrorMessage}.',"idb-set":'Error thrown when writing to IndexedDB. Original error: {$originalErrorMessage}.',"idb-delete":'Error thrown when deleting from IndexedDB. Original error: {$originalErrorMessage}.',"finalization-registry-not-supported":'FirebaseServerApp deleteOnDeref field defined but the JS runtime does not support FinalizationRegistry.',"invalid-server-app-environment":'FirebaseServerApp is not for use in browser environments.'},te=new n.ErrorFactory('app','Firebase',ee);
/**
   * @license
   * Copyright 2019 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */
class re{constructor(t,n,i){this._isDeleted=!1,this._options=Object.assign({},t),this._config=Object.assign({},n),this._name=n.name,this._automaticDataCollectionEnabled=n.automaticDataCollectionEnabled,this._container=i,this.container.addComponent(new e.Component('app',()=>this,"PUBLIC"))}get automaticDataCollectionEnabled(){return this.checkDestroyed(),this._automaticDataCollectionEnabled}set automaticDataCollectionEnabled(e){this.checkDestroyed(),this._automaticDataCollectionEnabled=e}get name(){return this.checkDestroyed(),this._name}get options(){return this.checkDestroyed(),this._options}get config(){return this.checkDestroyed(),this._config}get container(){return this._container}get isDeleted(){return this._isDeleted}set isDeleted(e){this._isDeleted=e}checkDestroyed(){if(this.isDeleted)throw te.create("app-deleted",{appName:this._name})}}
/**
   * @license
   * Copyright 2023 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */function ae(e,t){const i=(0,n.base64Decode)(e.split('.')[1]);if(null===i)return void console.error(`FirebaseServerApp ${t} is invalid: second part could not be parsed.`);if(void 0===JSON.parse(i).exp)return void console.error(`FirebaseServerApp ${t} is invalid: expiration claim could not be parsed`);1e3*JSON.parse(i).exp-(new Date).getTime()<=0&&console.error(`FirebaseServerApp ${t} is invalid: the token has expired.`)}class ne extends re{constructor(e,t,n,i){const o=void 0===t.automaticDataCollectionEnabled||t.automaticDataCollectionEnabled,s={name:n,automaticDataCollectionEnabled:o};if(void 0!==e.apiKey)super(e,s,i);else{super(e.options,s,i)}this._serverConfig=Object.assign({automaticDataCollectionEnabled:o},t),this._serverConfig.authIdToken&&ae(this._serverConfig.authIdToken,'authIdToken'),this._serverConfig.appCheckToken&&ae(this._serverConfig.appCheckToken,'appCheckToken'),this._finalizationRegistry=null,'undefined'!=typeof FinalizationRegistry&&(this._finalizationRegistry=new FinalizationRegistry(()=>{this.automaticCleanup()})),this._refCount=0,this.incRefCount(this._serverConfig.releaseOnDeref),this._serverConfig.releaseOnDeref=void 0,t.releaseOnDeref=void 0,le(c,p,'serverapp')}toJSON(){}get refCount(){return this._refCount}incRefCount(e){this.isDeleted||(this._refCount++,void 0!==e&&null!==this._finalizationRegistry&&this._finalizationRegistry.register(e,this))}decRefCount(){return this.isDeleted?0:--this._refCount}automaticCleanup(){fe(this)}get settings(){return this.checkDestroyed(),this._serverConfig}checkDestroyed(){if(this.isDeleted)throw te.create("server-app-deleted")}}
/**
   * @license
   * Copyright 2019 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */const ie="12.12.0";function oe(t,i={}){let o=t;if('object'!=typeof i){i={name:i}}const s=Object.assign({name:H,automaticDataCollectionEnabled:!0},i),c=s.name;if('string'!=typeof c||!c)throw te.create("bad-app-name",{appName:String(c)});if(o||(o=(0,n.getDefaultAppConfig)()),!o)throw te.create("no-options");const p=L.get(c);if(p){if((0,n.deepEqual)(o,p.options)&&(0,n.deepEqual)(s,p.config))return p;throw te.create("duplicate-app",{appName:c})}const f=new e.ComponentContainer(c);for(const e of J.values())f.addComponent(e);const l=new re(o,s,f);return L.set(c,l),l}function se(t,i={}){if((0,n.isBrowser)()&&!(0,n.isWebWorker)())throw te.create("invalid-server-app-environment");let o,s=i||{};if(t&&(G(t)?o=t.options:Q(t)?s=t:o=t),void 0===s.automaticDataCollectionEnabled&&(s.automaticDataCollectionEnabled=!0),o||(o=(0,n.getDefaultAppConfig)()),!o)throw te.create("no-options");const c=Object.assign({},s,o);void 0!==c.releaseOnDeref&&delete c.releaseOnDeref;if(void 0!==s.releaseOnDeref&&'undefined'==typeof FinalizationRegistry)throw te.create("finalization-registry-not-supported",{});const p=''+(f=JSON.stringify(c),[...f].reduce((e,t)=>Math.imul(31,e)+t.charCodeAt(0)|0,0));var f;const l=U.get(p);if(l)return l.incRefCount(s.releaseOnDeref),l;const h=new e.ComponentContainer(p);for(const e of J.values())h.addComponent(e);const u=new ne(o,s,p,h);return U.set(p,u),u}function ce(e=H){const t=L.get(e);if(!t&&e===H&&(0,n.getDefaultAppConfig)())return oe();if(!t)throw te.create("no-app",{appName:e});return t}function pe(){return Array.from(L.values())}async function fe(e){let t=!1;const n=e.name;if(L.has(n))t=!0,L.delete(n);else if(U.has(n)){e.decRefCount()<=0&&(U.delete(n),t=!0)}t&&(await Promise.all(e.container.getProviders().map(e=>e.delete())),e.isDeleted=!0)}function le(t,n,i){let o=M[t]??t;i&&(o+=`-${i}`);const s=o.match(/\s|\//),c=n.match(/\s|\//);if(s||c){const e=[`Unable to register library "${o}" with version "${n}":`];return s&&e.push(`library name "${o}" contains illegal characters (whitespace or "/")`),s&&c&&e.push('and'),c&&e.push(`version name "${n}" contains illegal characters (whitespace or "/")`),void f.warn(e.join(' '))}q(new e.Component(`${o}-version`,()=>({library:o,version:n}),"VERSION"))}function he(e,n){if(null!==e&&'function'!=typeof e)throw te.create("invalid-log-argument");(0,t.setUserLogHandler)(e,n)}function ue(e){(0,t.setLogLevel)(e)}
/**
   * @license
   * Copyright 2021 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */const de='firebase-heartbeat-store';let be=null;function ge(){return be||(be=(0,i.openDB)("firebase-heartbeat-database",1,{upgrade:(e,t)=>{if(0===t)try{e.createObjectStore(de)}catch(e){console.warn(e)}}}).catch(e=>{throw te.create("idb-open",{originalErrorMessage:e.message})})),be}async function me(e){try{const t=(await ge()).transaction(de),n=await t.objectStore(de).get(Ce(e));return await t.done,n}catch(e){if(e instanceof n.FirebaseError)f.warn(e.message);else{const t=te.create("idb-get",{originalErrorMessage:e?.message});f.warn(t.message)}}}async function ve(e,t){try{const n=(await ge()).transaction(de,'readwrite'),i=n.objectStore(de);await i.put(t,Ce(e)),await n.done}catch(e){if(e instanceof n.FirebaseError)f.warn(e.message);else{const t=te.create("idb-set",{originalErrorMessage:e?.message});f.warn(t.message)}}}function Ce(e){return`${e.name}!${e.options.appId}`}
/**
   * @license
   * Copyright 2021 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */class ye{constructor(e){this.container=e,this._heartbeatsCache=null;const t=this.container.getProvider('app').getImmediate();this._storage=new Oe(t),this._heartbeatsCachePromise=this._storage.read().then(e=>(this._heartbeatsCache=e,e))}async triggerHeartbeat(){try{const e=this.container.getProvider('platform-logger').getImmediate().getPlatformInfoString(),t=we();if(null==this._heartbeatsCache?.heartbeats&&(this._heartbeatsCache=await this._heartbeatsCachePromise,null==this._heartbeatsCache?.heartbeats))return;if(this._heartbeatsCache.lastSentHeartbeatDate===t||this._heartbeatsCache.heartbeats.some(e=>e.date===t))return;if(this._heartbeatsCache.heartbeats.push({date:t,agent:e}),this._heartbeatsCache.heartbeats.length>30){const e=Pe(this._heartbeatsCache.heartbeats);this._heartbeatsCache.heartbeats.splice(e,1)}return this._storage.overwrite(this._heartbeatsCache)}catch(e){f.warn(e)}}async getHeartbeatsHeader(){try{if(null===this._heartbeatsCache&&await this._heartbeatsCachePromise,null==this._heartbeatsCache?.heartbeats||0===this._heartbeatsCache.heartbeats.length)return'';const e=we(),{heartbeatsToSend:t,unsentEntries:i}=De(this._heartbeatsCache.heartbeats),o=(0,n.base64urlEncodeWithoutPadding)(JSON.stringify({version:2,heartbeats:t}));return this._heartbeatsCache.lastSentHeartbeatDate=e,i.length>0?(this._heartbeatsCache.heartbeats=i,await this._storage.overwrite(this._heartbeatsCache)):(this._heartbeatsCache.heartbeats=[],this._storage.overwrite(this._heartbeatsCache)),o}catch(e){return f.warn(e),''}}}function we(){return(new Date).toISOString().substring(0,10)}function De(e,t=1024){const n=[];let i=e.slice();for(const o of e){const e=n.find(e=>e.agent===o.agent);if(e){if(e.dates.push(o.date),Ee(n)>t){e.dates.pop();break}}else if(n.push({agent:o.agent,dates:[o.date]}),Ee(n)>t){n.pop();break}i=i.slice(1)}return{heartbeatsToSend:n,unsentEntries:i}}class Oe{constructor(e){this.app=e,this._canUseIndexedDBPromise=this.runIndexedDBEnvironmentCheck()}async runIndexedDBEnvironmentCheck(){return!!(0,n.isIndexedDBAvailable)()&&(0,n.validateIndexedDBOpenable)().then(()=>!0).catch(()=>!1)}async read(){if(await this._canUseIndexedDBPromise){const e=await me(this.app);return e?.heartbeats?e:{heartbeats:[]}}return{heartbeats:[]}}async overwrite(e){if(await this._canUseIndexedDBPromise){const t=await this.read();return ve(this.app,{lastSentHeartbeatDate:e.lastSentHeartbeatDate??t.lastSentHeartbeatDate,heartbeats:e.heartbeats})}}async add(e){if(await this._canUseIndexedDBPromise){const t=await this.read();return ve(this.app,{lastSentHeartbeatDate:e.lastSentHeartbeatDate??t.lastSentHeartbeatDate,heartbeats:[...t.heartbeats,...e.heartbeats]})}}}function Ee(e){return(0,n.base64urlEncodeWithoutPadding)(JSON.stringify({version:2,heartbeats:e})).length}function Pe(e){if(0===e.length)return-1;let t=0,n=e[0].date;for(let i=1;i<e.length;i++)e[i].date<n&&(n=e[i].date,t=i);return t}
/**
   * @license
   * Copyright 2019 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */var Se;Se='',q(new e.Component('platform-logger',e=>new o(e),"PRIVATE")),q(new e.Component('heartbeat',e=>new ye(e),"PRIVATE")),le(c,p,Se),le(c,p,'esm2020'),le('fire-js','')},1763,[1768,1767,1766,1837]);
__d(function(g,r,_i,_a,m,_e,_d){"use strict";Object.defineProperty(_e,'__esModule',{value:!0}),Object.defineProperty(_e,"CONSTANTS",{enumerable:!0,get:function(){return t}}),Object.defineProperty(_e,"DecodeBase64StringError",{enumerable:!0,get:function(){return u}}),Object.defineProperty(_e,"Deferred",{enumerable:!0,get:function(){return v}}),Object.defineProperty(_e,"ErrorFactory",{enumerable:!0,get:function(){return H}}),Object.defineProperty(_e,"FirebaseError",{enumerable:!0,get:function(){return z}}),Object.defineProperty(_e,"MAX_VALUE_MILLIS",{enumerable:!0,get:function(){return we}}),Object.defineProperty(_e,"RANDOM_FACTOR",{enumerable:!0,get:function(){return Ce}}),Object.defineProperty(_e,"Sha1",{enumerable:!0,get:function(){return le}}),Object.defineProperty(_e,"areCookiesEnabled",{enumerable:!0,get:function(){return $}}),Object.defineProperty(_e,"assert",{enumerable:!0,get:function(){return n}}),Object.defineProperty(_e,"assertionError",{enumerable:!0,get:function(){return o}}),Object.defineProperty(_e,"async",{enumerable:!0,get:function(){return be}}),Object.defineProperty(_e,"base64",{enumerable:!0,get:function(){return c}}),Object.defineProperty(_e,"base64Decode",{enumerable:!0,get:function(){return l}}),Object.defineProperty(_e,"base64Encode",{enumerable:!0,get:function(){return a}}),Object.defineProperty(_e,"base64urlEncodeWithoutPadding",{enumerable:!0,get:function(){return f}}),Object.defineProperty(_e,"calculateBackoffMillis",{enumerable:!0,get:function(){return De}}),Object.defineProperty(_e,"contains",{enumerable:!0,get:function(){return te}}),Object.defineProperty(_e,"createMockUserToken",{enumerable:!0,get:function(){return A}}),Object.defineProperty(_e,"createSubscribe",{enumerable:!0,get:function(){return he}}),Object.defineProperty(_e,"decode",{enumerable:!0,get:function(){return Q}}),Object.defineProperty(_e,"deepCopy",{enumerable:!0,get:function(){return h}}),Object.defineProperty(_e,"deepEqual",{enumerable:!0,get:function(){return ie}}),Object.defineProperty(_e,"deepExtend",{enumerable:!0,get:function(){return d}}),Object.defineProperty(_e,"errorPrefix",{enumerable:!0,get:function(){return me}}),Object.defineProperty(_e,"extractQuerystring",{enumerable:!0,get:function(){return fe}}),Object.defineProperty(_e,"generateSHA256Hash",{enumerable:!0,get:function(){return xe}}),Object.defineProperty(_e,"getDefaultAppConfig",{enumerable:!0,get:function(){return S}}),Object.defineProperty(_e,"getDefaultEmulatorHost",{enumerable:!0,get:function(){return j}}),Object.defineProperty(_e,"getDefaultEmulatorHostnameAndPort",{enumerable:!0,get:function(){return E}}),Object.defineProperty(_e,"getDefaults",{enumerable:!0,get:function(){return _}}),Object.defineProperty(_e,"getExperimentalSetting",{enumerable:!0,get:function(){return P}}),Object.defineProperty(_e,"getGlobal",{enumerable:!0,get:function(){return p}}),Object.defineProperty(_e,"getModularInstance",{enumerable:!0,get:function(){return ke}}),Object.defineProperty(_e,"getUA",{enumerable:!0,get:function(){return w}}),Object.defineProperty(_e,"isAdmin",{enumerable:!0,get:function(){return ee}}),Object.defineProperty(_e,"isBrowser",{enumerable:!0,get:function(){return T}}),Object.defineProperty(_e,"isBrowserExtension",{enumerable:!0,get:function(){return M}}),Object.defineProperty(_e,"isCloudWorkstation",{enumerable:!0,get:function(){return Me}}),Object.defineProperty(_e,"isCloudflareWorker",{enumerable:!0,get:function(){return k}}),Object.defineProperty(_e,"isElectron",{enumerable:!0,get:function(){return x}}),Object.defineProperty(_e,"isEmpty",{enumerable:!0,get:function(){return ne}}),Object.defineProperty(_e,"isIE",{enumerable:!0,get:function(){return I}}),Object.defineProperty(_e,"isIndexedDBAvailable",{enumerable:!0,get:function(){return F}}),Object.defineProperty(_e,"isMobileCordova",{enumerable:!0,get:function(){return C}}),Object.defineProperty(_e,"isNode",{enumerable:!0,get:function(){return D}}),Object.defineProperty(_e,"isNodeSdk",{enumerable:!0,get:function(){return L}}),Object.defineProperty(_e,"isReactNative",{enumerable:!0,get:function(){return B}}),Object.defineProperty(_e,"isSafari",{enumerable:!0,get:function(){return R}}),Object.defineProperty(_e,"isSafariOrWebkit",{enumerable:!0,get:function(){return U}}),Object.defineProperty(_e,"isUWP",{enumerable:!0,get:function(){return W}}),Object.defineProperty(_e,"isValidFormat",{enumerable:!0,get:function(){return Z}}),Object.defineProperty(_e,"isValidTimestamp",{enumerable:!0,get:function(){return X}}),Object.defineProperty(_e,"isWebWorker",{enumerable:!0,get:function(){return N}}),Object.defineProperty(_e,"issuedAtTime",{enumerable:!0,get:function(){return Y}}),Object.defineProperty(_e,"jsonEval",{enumerable:!0,get:function(){return q}}),Object.defineProperty(_e,"map",{enumerable:!0,get:function(){return oe}}),Object.defineProperty(_e,"ordinal",{enumerable:!0,get:function(){return Te}}),Object.defineProperty(_e,"pingServer",{enumerable:!0,get:function(){return Be}}),Object.defineProperty(_e,"promiseWithTimeout",{enumerable:!0,get:function(){return ce}}),Object.defineProperty(_e,"querystring",{enumerable:!0,get:function(){return ue}}),Object.defineProperty(_e,"querystringDecode",{enumerable:!0,get:function(){return ae}}),Object.defineProperty(_e,"safeGet",{enumerable:!0,get:function(){return re}}),Object.defineProperty(_e,"stringLength",{enumerable:!0,get:function(){return Pe}}),Object.defineProperty(_e,"stringToByteArray",{enumerable:!0,get:function(){return Se}}),Object.defineProperty(_e,"stringify",{enumerable:!0,get:function(){return K}}),Object.defineProperty(_e,"validateArgCount",{enumerable:!0,get:function(){return ye}}),Object.defineProperty(_e,"validateCallback",{enumerable:!0,get:function(){return je}}),Object.defineProperty(_e,"validateContextObject",{enumerable:!0,get:function(){return Ee}}),Object.defineProperty(_e,"validateIndexedDBOpenable",{enumerable:!0,get:function(){return V}}),Object.defineProperty(_e,"validateNamespace",{enumerable:!0,get:function(){return Oe}});var e=r(_d[0]);
/**
   * @license
   * Copyright 2017 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */const t={NODE_CLIENT:!1,NODE_ADMIN:!1,SDK_VERSION:'${JSCORE_VERSION}'},n=function(e,t){if(!e)throw o(t)},o=function(e){return new Error('Firebase Database ('+t.SDK_VERSION+') INTERNAL ASSERT FAILED: '+e)},i=function(e){const t=[];let n=0;for(let o=0;o<e.length;o++){let i=e.charCodeAt(o);i<128?t[n++]=i:i<2048?(t[n++]=i>>6|192,t[n++]=63&i|128):55296==(64512&i)&&o+1<e.length&&56320==(64512&e.charCodeAt(o+1))?(i=65536+((1023&i)<<10)+(1023&e.charCodeAt(++o)),t[n++]=i>>18|240,t[n++]=i>>12&63|128,t[n++]=i>>6&63|128,t[n++]=63&i|128):(t[n++]=i>>12|224,t[n++]=i>>6&63|128,t[n++]=63&i|128)}return t},s=function(e){const t=[];let n=0,o=0;for(;n<e.length;){const i=e[n++];if(i<128)t[o++]=String.fromCharCode(i);else if(i>191&&i<224){const s=e[n++];t[o++]=String.fromCharCode((31&i)<<6|63&s)}else if(i>239&&i<365){const s=((7&i)<<18|(63&e[n++])<<12|(63&e[n++])<<6|63&e[n++])-65536;t[o++]=String.fromCharCode(55296+(s>>10)),t[o++]=String.fromCharCode(56320+(1023&s))}else{const s=e[n++],c=e[n++];t[o++]=String.fromCharCode((15&i)<<12|(63&s)<<6|63&c)}}return t.join('')},c={byteToCharMap_:null,charToByteMap_:null,byteToCharMapWebSafe_:null,charToByteMapWebSafe_:null,ENCODED_VALS_BASE:"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",get ENCODED_VALS(){return this.ENCODED_VALS_BASE+'+/='},get ENCODED_VALS_WEBSAFE(){return this.ENCODED_VALS_BASE+'-_.'},HAS_NATIVE_SUPPORT:'function'==typeof atob,encodeByteArray(e,t){if(!Array.isArray(e))throw Error('encodeByteArray takes an array as a parameter');this.init_();const n=t?this.byteToCharMapWebSafe_:this.byteToCharMap_,o=[];for(let t=0;t<e.length;t+=3){const i=e[t],s=t+1<e.length,c=s?e[t+1]:0,u=t+2<e.length,a=u?e[t+2]:0,f=i>>2,l=(3&i)<<4|c>>4;let h=(15&c)<<2|a>>6,d=63&a;u||(d=64,s||(h=64)),o.push(n[f],n[l],n[h],n[d])}return o.join('')},encodeString(e,t){return this.HAS_NATIVE_SUPPORT&&!t?btoa(e):this.encodeByteArray(i(e),t)},decodeString(e,t){return this.HAS_NATIVE_SUPPORT&&!t?atob(e):s(this.decodeStringToByteArray(e,t))},decodeStringToByteArray(e,t){this.init_();const n=t?this.charToByteMapWebSafe_:this.charToByteMap_,o=[];for(let t=0;t<e.length;){const i=n[e.charAt(t++)],s=t<e.length?n[e.charAt(t)]:0;++t;const c=t<e.length?n[e.charAt(t)]:64;++t;const a=t<e.length?n[e.charAt(t)]:64;if(++t,null==i||null==s||null==c||null==a)throw new u;const f=i<<2|s>>4;if(o.push(f),64!==c){const e=s<<4&240|c>>2;if(o.push(e),64!==a){const e=c<<6&192|a;o.push(e)}}}return o},init_(){if(!this.byteToCharMap_){this.byteToCharMap_={},this.charToByteMap_={},this.byteToCharMapWebSafe_={},this.charToByteMapWebSafe_={};for(let e=0;e<this.ENCODED_VALS.length;e++)this.byteToCharMap_[e]=this.ENCODED_VALS.charAt(e),this.charToByteMap_[this.byteToCharMap_[e]]=e,this.byteToCharMapWebSafe_[e]=this.ENCODED_VALS_WEBSAFE.charAt(e),this.charToByteMapWebSafe_[this.byteToCharMapWebSafe_[e]]=e,e>=this.ENCODED_VALS_BASE.length&&(this.charToByteMap_[this.ENCODED_VALS_WEBSAFE.charAt(e)]=e,this.charToByteMapWebSafe_[this.ENCODED_VALS.charAt(e)]=e)}}};
/**
   * @license
   * Copyright 2017 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */class u extends Error{constructor(){super(...arguments),this.name='DecodeBase64StringError'}}const a=function(e){const t=i(e);return c.encodeByteArray(t,!0)},f=function(e){return a(e).replace(/\./g,'')},l=function(e){try{return c.decodeString(e,!0)}catch(e){console.error('base64Decode failed: ',e)}return null};
/**
   * @license
   * Copyright 2017 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */
function h(e){return d(void 0,e)}function d(e,t){if(!(t instanceof Object))return t;switch(t.constructor){case Date:return new Date(t.getTime());case Object:void 0===e&&(e={});break;case Array:e=[];break;default:return t}for(const n in t)t.hasOwnProperty(n)&&b(n)&&(e[n]=d(e[n],t[n]));return e}function b(e){return'__proto__'!==e}
/**
   * @license
   * Copyright 2022 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */function p(){if('undefined'!=typeof self)return self;if('undefined'!=typeof window)return window;if(void 0!==g)return g;throw new Error('Unable to locate global object.')}
/**
   * @license
   * Copyright 2022 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */const y=()=>{if('undefined'==typeof process||void 0===process.env)return;const e=process.env.__FIREBASE_DEFAULTS__;return e?JSON.parse(e):void 0},O=()=>{if('undefined'==typeof document)return;let e;try{e=document.cookie.match(/__FIREBASE_DEFAULTS__=([^;]+)/)}catch(e){return}const t=e&&l(e[1]);return t&&JSON.parse(t)},_=()=>{try{return(0,e.getDefaultsFromPostinstall)()||p().__FIREBASE_DEFAULTS__||y()||O()}catch(e){return void console.info(`Unable to get __FIREBASE_DEFAULTS__ due to: ${e}`)}},j=e=>_()?.emulatorHosts?.[e],E=e=>{const t=j(e);if(!t)return;const n=t.lastIndexOf(':');if(n<=0||n+1===t.length)throw new Error(`Invalid host ${t} with no separate hostname and port!`);const o=parseInt(t.substring(n+1),10);return'['===t[0]?[t.substring(1,n-1),o]:[t.substring(0,n),o]},S=()=>_()?.config,P=e=>_()?.[`_${e}`];
/**
   * @license
   * Copyright 2017 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */
class v{constructor(){this.reject=()=>{},this.resolve=()=>{},this.promise=new Promise((e,t)=>{this.resolve=e,this.reject=t})}wrapCallback(e){return(t,n)=>{t?this.reject(t):this.resolve(n),'function'==typeof e&&(this.promise.catch(()=>{}),1===e.length?e(t):e(t,n))}}}
/**
   * @license
   * Copyright 2021 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */function A(e,t){if(e.uid)throw new Error('The "uid" field is no longer supported by mockUserToken. Please use "sub" instead for Firebase Auth User ID.');const n=t||'demo-project',o=e.iat||0,i=e.sub||e.user_id;if(!i)throw new Error("mockUserToken must contain 'sub' or 'user_id' field!");const s=Object.assign({iss:`https://securetoken.google.com/${n}`,aud:n,iat:o,exp:o+3600,auth_time:o,sub:i,user_id:i,firebase:{sign_in_provider:'custom',identities:{}}},e);return[f(JSON.stringify({alg:'none',type:'JWT'})),f(JSON.stringify(s)),''].join('.')}
/**
   * @license
   * Copyright 2017 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */function w(){return'undefined'!=typeof navigator&&'string'==typeof navigator.userAgent?navigator.userAgent:''}function C(){return'undefined'!=typeof window&&!!(window.cordova||window.phonegap||window.PhoneGap)&&/ios|iphone|ipod|ipad|android|blackberry|iemobile/i.test(w())}function D(){const e=_()?.forceEnvironment;if('node'===e)return!0;if('browser'===e)return!1;try{return'[object process]'===Object.prototype.toString.call(g.process)}catch(e){return!1}}function T(){return'undefined'!=typeof window||N()}function N(){return'undefined'!=typeof WorkerGlobalScope&&'undefined'!=typeof self&&self instanceof WorkerGlobalScope}function k(){return'undefined'!=typeof navigator&&'Cloudflare-Workers'===navigator.userAgent}function M(){const e='object'==typeof chrome?chrome.runtime:'object'==typeof browser?browser.runtime:void 0;return'object'==typeof e&&void 0!==e.id}function B(){return'object'==typeof navigator&&'ReactNative'===navigator.product}function x(){return w().indexOf('Electron/')>=0}function I(){const e=w();return e.indexOf('MSIE ')>=0||e.indexOf('Trident/')>=0}function W(){return w().indexOf('MSAppHost/')>=0}function L(){return!0===t.NODE_CLIENT||!0===t.NODE_ADMIN}function R(){return!D()&&!!navigator.userAgent&&navigator.userAgent.includes('Safari')&&!navigator.userAgent.includes('Chrome')}function U(){return!D()&&!!navigator.userAgent&&(navigator.userAgent.includes('Safari')||navigator.userAgent.includes('WebKit'))&&!navigator.userAgent.includes('Chrome')}function F(){try{return'object'==typeof indexedDB}catch(e){return!1}}function V(){return new Promise((e,t)=>{try{let n=!0;const o='validate-browser-context-for-indexeddb-analytics-module',i=self.indexedDB.open(o);i.onsuccess=()=>{i.result.close(),n||self.indexedDB.deleteDatabase(o),e(!0)},i.onupgradeneeded=()=>{n=!1},i.onerror=()=>{t(i.error?.message||'')}}catch(e){t(e)}})}function $(){return!('undefined'==typeof navigator||!navigator.cookieEnabled)}
/**
   * @license
   * Copyright 2017 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */class z extends Error{constructor(e,t,n){super(t),this.code=e,this.customData=n,this.name="FirebaseError",Object.setPrototypeOf(this,z.prototype),Error.captureStackTrace&&Error.captureStackTrace(this,H.prototype.create)}}class H{constructor(e,t,n){this.service=e,this.serviceName=t,this.errors=n}create(e,...t){const n=t[0]||{},o=`${this.service}/${e}`,i=this.errors[e],s=i?J(i,n):'Error',c=`${this.serviceName}: ${s} (${o}).`;return new z(o,c,n)}}function J(e,t){return e.replace(G,(e,n)=>{const o=t[n];return null!=o?String(o):`<${n}?>`})}const G=/\{\$([^}]+)}/g;
/**
   * @license
   * Copyright 2017 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */function q(e){return JSON.parse(e)}function K(e){return JSON.stringify(e)}
/**
   * @license
   * Copyright 2017 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */const Q=function(e){let t={},n={},o={},i='';try{const s=e.split('.');t=q(l(s[0])||''),n=q(l(s[1])||''),i=s[2],o=n.d||{},delete n.d}catch(e){}return{header:t,claims:n,data:o,signature:i}},X=function(e){const t=Q(e).claims,n=Math.floor((new Date).getTime()/1e3);let o=0,i=0;return'object'==typeof t&&(t.hasOwnProperty('nbf')?o=t.nbf:t.hasOwnProperty('iat')&&(o=t.iat),i=t.hasOwnProperty('exp')?t.exp:o+86400),!!n&&!!o&&!!i&&n>=o&&n<=i},Y=function(e){const t=Q(e).claims;return'object'==typeof t&&t.hasOwnProperty('iat')?t.iat:null},Z=function(e){const t=Q(e).claims;return!!t&&'object'==typeof t&&t.hasOwnProperty('iat')},ee=function(e){const t=Q(e).claims;return'object'==typeof t&&!0===t.admin};
/**
   * @license
   * Copyright 2017 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */
function te(e,t){return Object.prototype.hasOwnProperty.call(e,t)}function re(e,t){return Object.prototype.hasOwnProperty.call(e,t)?e[t]:void 0}function ne(e){for(const t in e)if(Object.prototype.hasOwnProperty.call(e,t))return!1;return!0}function oe(e,t,n){const o={};for(const i in e)Object.prototype.hasOwnProperty.call(e,i)&&(o[i]=t.call(n,e[i],i,e));return o}function ie(e,t){if(e===t)return!0;const n=Object.keys(e),o=Object.keys(t);for(const i of n){if(!o.includes(i))return!1;const n=e[i],s=t[i];if(se(n)&&se(s)){if(!ie(n,s))return!1}else if(n!==s)return!1}for(const e of o)if(!n.includes(e))return!1;return!0}function se(e){return null!==e&&'object'==typeof e}
/**
   * @license
   * Copyright 2022 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */function ce(e,t=2e3){const n=new v;return setTimeout(()=>n.reject('timeout!'),t),e.then(n.resolve,n.reject),n.promise}
/**
   * @license
   * Copyright 2017 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */function ue(e){const t=[];for(const[n,o]of Object.entries(e))Array.isArray(o)?o.forEach(e=>{t.push(encodeURIComponent(n)+'='+encodeURIComponent(e))}):t.push(encodeURIComponent(n)+'='+encodeURIComponent(o));return t.length?'&'+t.join('&'):''}function ae(e){const t={};return e.replace(/^\?/,'').split('&').forEach(e=>{if(e){const[n,o]=e.split('=');t[decodeURIComponent(n)]=decodeURIComponent(o)}}),t}function fe(e){const t=e.indexOf('?');if(!t)return'';const n=e.indexOf('#',t);return e.substring(t,n>0?n:void 0)}
/**
   * @license
   * Copyright 2017 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */class le{constructor(){this.chain_=[],this.buf_=[],this.W_=[],this.pad_=[],this.inbuf_=0,this.total_=0,this.blockSize=64,this.pad_[0]=128;for(let e=1;e<this.blockSize;++e)this.pad_[e]=0;this.reset()}reset(){this.chain_[0]=1732584193,this.chain_[1]=4023233417,this.chain_[2]=2562383102,this.chain_[3]=271733878,this.chain_[4]=3285377520,this.inbuf_=0,this.total_=0}compress_(e,t){t||(t=0);const n=this.W_;if('string'==typeof e)for(let o=0;o<16;o++)n[o]=e.charCodeAt(t)<<24|e.charCodeAt(t+1)<<16|e.charCodeAt(t+2)<<8|e.charCodeAt(t+3),t+=4;else for(let o=0;o<16;o++)n[o]=e[t]<<24|e[t+1]<<16|e[t+2]<<8|e[t+3],t+=4;for(let e=16;e<80;e++){const t=n[e-3]^n[e-8]^n[e-14]^n[e-16];n[e]=4294967295&(t<<1|t>>>31)}let o,i,s=this.chain_[0],c=this.chain_[1],u=this.chain_[2],a=this.chain_[3],f=this.chain_[4];for(let e=0;e<80;e++){e<40?e<20?(o=a^c&(u^a),i=1518500249):(o=c^u^a,i=1859775393):e<60?(o=c&u|a&(c|u),i=2400959708):(o=c^u^a,i=3395469782);const t=(s<<5|s>>>27)+o+f+i+n[e]&4294967295;f=a,a=u,u=4294967295&(c<<30|c>>>2),c=s,s=t}this.chain_[0]=this.chain_[0]+s&4294967295,this.chain_[1]=this.chain_[1]+c&4294967295,this.chain_[2]=this.chain_[2]+u&4294967295,this.chain_[3]=this.chain_[3]+a&4294967295,this.chain_[4]=this.chain_[4]+f&4294967295}update(e,t){if(null==e)return;void 0===t&&(t=e.length);const n=t-this.blockSize;let o=0;const i=this.buf_;let s=this.inbuf_;for(;o<t;){if(0===s)for(;o<=n;)this.compress_(e,o),o+=this.blockSize;if('string'==typeof e){for(;o<t;)if(i[s]=e.charCodeAt(o),++s,++o,s===this.blockSize){this.compress_(i),s=0;break}}else for(;o<t;)if(i[s]=e[o],++s,++o,s===this.blockSize){this.compress_(i),s=0;break}}this.inbuf_=s,this.total_+=t}digest(){const e=[];let t=8*this.total_;this.inbuf_<56?this.update(this.pad_,56-this.inbuf_):this.update(this.pad_,this.blockSize-(this.inbuf_-56));for(let e=this.blockSize-1;e>=56;e--)this.buf_[e]=255&t,t/=256;this.compress_(this.buf_);let n=0;for(let t=0;t<5;t++)for(let o=24;o>=0;o-=8)e[n]=this.chain_[t]>>o&255,++n;return e}}function he(e,t){const n=new de(e,t);return n.subscribe.bind(n)}class de{constructor(e,t){this.observers=[],this.unsubscribes=[],this.observerCount=0,this.task=Promise.resolve(),this.finalized=!1,this.onNoObservers=t,this.task.then(()=>{e(this)}).catch(e=>{this.error(e)})}next(e){this.forEachObserver(t=>{t.next(e)})}error(e){this.forEachObserver(t=>{t.error(e)}),this.close(e)}complete(){this.forEachObserver(e=>{e.complete()}),this.close()}subscribe(e,t,n){let o;if(void 0===e&&void 0===t&&void 0===n)throw new Error('Missing Observer.');o=pe(e,['next','error','complete'])?e:{next:e,error:t,complete:n},void 0===o.next&&(o.next=ge),void 0===o.error&&(o.error=ge),void 0===o.complete&&(o.complete=ge);const i=this.unsubscribeOne.bind(this,this.observers.length);return this.finalized&&this.task.then(()=>{try{this.finalError?o.error(this.finalError):o.complete()}catch(e){}}),this.observers.push(o),i}unsubscribeOne(e){void 0!==this.observers&&void 0!==this.observers[e]&&(delete this.observers[e],this.observerCount-=1,0===this.observerCount&&void 0!==this.onNoObservers&&this.onNoObservers(this))}forEachObserver(e){if(!this.finalized)for(let t=0;t<this.observers.length;t++)this.sendOne(t,e)}sendOne(e,t){this.task.then(()=>{if(void 0!==this.observers&&void 0!==this.observers[e])try{t(this.observers[e])}catch(e){'undefined'!=typeof console&&console.error&&console.error(e)}})}close(e){this.finalized||(this.finalized=!0,void 0!==e&&(this.finalError=e),this.task.then(()=>{this.observers=void 0,this.onNoObservers=void 0}))}}function be(e,t){return(...n)=>{Promise.resolve(!0).then(()=>{e(...n)}).catch(e=>{t&&t(e)})}}function pe(e,t){if('object'!=typeof e||null===e)return!1;for(const n of t)if(n in e&&'function'==typeof e[n])return!0;return!1}function ge(){}
/**
   * @license
   * Copyright 2017 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */const ye=function(e,t,n,o){let i;if(o<t?i='at least '+t:o>n&&(i=0===n?'none':'no more than '+n),i){throw new Error(e+' failed: Was called with '+o+(1===o?' argument.':' arguments.')+' Expects '+i+'.')}};function me(e,t){return`${e} failed: ${t} argument `}function Oe(e,t,n){if((!n||t)&&'string'!=typeof t)throw new Error(me(e,'namespace')+'must be a valid firebase namespace.')}function je(e,t,n,o){if((!o||n)&&'function'!=typeof n)throw new Error(me(e,t)+'must be a valid function.')}function Ee(e,t,n,o){if((!o||n)&&('object'!=typeof n||null===n))throw new Error(me(e,t)+'must be a valid context object.')}
/**
   * @license
   * Copyright 2017 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */const Se=function(e){const t=[];let o=0;for(let i=0;i<e.length;i++){let s=e.charCodeAt(i);if(s>=55296&&s<=56319){const t=s-55296;i++,n(i<e.length,'Surrogate pair missing trail surrogate.');s=65536+(t<<10)+(e.charCodeAt(i)-56320)}s<128?t[o++]=s:s<2048?(t[o++]=s>>6|192,t[o++]=63&s|128):s<65536?(t[o++]=s>>12|224,t[o++]=s>>6&63|128,t[o++]=63&s|128):(t[o++]=s>>18|240,t[o++]=s>>12&63|128,t[o++]=s>>6&63|128,t[o++]=63&s|128)}return t},Pe=function(e){let t=0;for(let n=0;n<e.length;n++){const o=e.charCodeAt(n);o<128?t++:o<2048?t+=2:o>=55296&&o<=56319?(t+=4,n++):t+=3}return t},ve=1e3,Ae=2,we=144e5,Ce=.5;function De(e,t=ve,n=Ae){const o=t*Math.pow(n,e),i=Math.round(Ce*o*(Math.random()-.5)*2);return Math.min(we,o+i)}
/**
   * @license
   * Copyright 2020 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */function Te(e){return Number.isFinite(e)?e+Ne(e):`${e}`}function Ne(e){const t=(e=Math.abs(e))%100;if(t>=10&&t<=20)return'th';const n=e%10;return 1===n?'st':2===n?'nd':3===n?'rd':'th'}
/**
   * @license
   * Copyright 2021 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */function ke(e){return e&&e._delegate?e._delegate:e}
/**
   * @license
   * Copyright 2025 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */function Me(e){try{return(e.startsWith('http://')||e.startsWith('https://')?new URL(e).hostname:e).endsWith('.cloudworkstations.dev')}catch{return!1}}async function Be(e){return(await fetch(e,{credentials:'include'})).ok}
/**
   * @license
   * Copyright 2025 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */async function xe(e){const t=(new TextEncoder).encode(e),n=await crypto.subtle.digest('SHA-256',t);return Array.from(new Uint8Array(n)).map(e=>e.toString(16).padStart(2,'0')).join('')}},1766,[1838]);
__d(function(g,r,i,a,m,e,d){"use strict";Object.defineProperty(e,'__esModule',{value:!0}),Object.defineProperty(e,"LogLevel",{enumerable:!0,get:function(){return n}}),Object.defineProperty(e,"Logger",{enumerable:!0,get:function(){return h}}),Object.defineProperty(e,"setLogLevel",{enumerable:!0,get:function(){return L}}),Object.defineProperty(e,"setUserLogHandler",{enumerable:!0,get:function(){return f}});
/**
   * @license
   * Copyright 2017 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */
const t=[];var n;!(function(t){t[t.DEBUG=0]="DEBUG",t[t.VERBOSE=1]="VERBOSE",t[t.INFO=2]="INFO",t[t.WARN=3]="WARN",t[t.ERROR=4]="ERROR",t[t.SILENT=5]="SILENT"})(n||(n={}));const o={debug:n.DEBUG,verbose:n.VERBOSE,info:n.INFO,warn:n.WARN,error:n.ERROR,silent:n.SILENT},l=n.INFO,s={[n.DEBUG]:'log',[n.VERBOSE]:'log',[n.INFO]:'info',[n.WARN]:'warn',[n.ERROR]:'error'},u=(t,n,...o)=>{if(n<t.logLevel)return;const l=(new Date).toISOString(),u=s[n];if(!u)throw new Error(`Attempted to log a message with an invalid logType (value: ${n})`);console[u](`[${l}]  ${t.name}:`,...o)};class h{constructor(n){this.name=n,this._logLevel=l,this._logHandler=u,this._userLogHandler=null,t.push(this)}get logLevel(){return this._logLevel}set logLevel(t){if(!(t in n))throw new TypeError(`Invalid value "${t}" assigned to \`logLevel\``);this._logLevel=t}setLogLevel(t){this._logLevel='string'==typeof t?o[t]:t}get logHandler(){return this._logHandler}set logHandler(t){if('function'!=typeof t)throw new TypeError('Value assigned to `logHandler` must be a function');this._logHandler=t}get userLogHandler(){return this._userLogHandler}set userLogHandler(t){this._userLogHandler=t}debug(...t){this._userLogHandler&&this._userLogHandler(this,n.DEBUG,...t),this._logHandler(this,n.DEBUG,...t)}log(...t){this._userLogHandler&&this._userLogHandler(this,n.VERBOSE,...t),this._logHandler(this,n.VERBOSE,...t)}info(...t){this._userLogHandler&&this._userLogHandler(this,n.INFO,...t),this._logHandler(this,n.INFO,...t)}warn(...t){this._userLogHandler&&this._userLogHandler(this,n.WARN,...t),this._logHandler(this,n.WARN,...t)}error(...t){this._userLogHandler&&this._userLogHandler(this,n.ERROR,...t),this._logHandler(this,n.ERROR,...t)}}function L(n){t.forEach(t=>{t.setLogLevel(n)})}function f(l,s){for(const u of t){let t=null;s&&s.level&&(t=o[s.level]),u.userLogHandler=null===l?null:(o,s,...u)=>{const h=u.map(t=>{if(null==t)return null;if('string'==typeof t)return t;if('number'==typeof t||'boolean'==typeof t)return t.toString();if(t instanceof Error)return t.message;try{return JSON.stringify(t)}catch(t){return null}}).filter(t=>t).join(' ');s>=(t??o.logLevel)&&l({level:n[s].toLowerCase(),message:h,args:u,type:o.name})}}}},1767,[]);
__d(function(g,r,i,a,m,_e,d){"use strict";Object.defineProperty(_e,'__esModule',{value:!0}),Object.defineProperty(_e,"Component",{enumerable:!0,get:function(){return t}}),Object.defineProperty(_e,"ComponentContainer",{enumerable:!0,get:function(){return c}}),Object.defineProperty(_e,"Provider",{enumerable:!0,get:function(){return s}});var e=r(d[0]);class t{constructor(e,t,n){this.name=e,this.instanceFactory=t,this.type=n,this.multipleInstances=!1,this.serviceProps={},this.instantiationMode="LAZY",this.onInstanceCreated=null}setInstantiationMode(e){return this.instantiationMode=e,this}setMultipleInstances(e){return this.multipleInstances=e,this}setServiceProps(e){return this.serviceProps=e,this}setInstanceCreatedCallback(e){return this.onInstanceCreated=e,this}}
/**
   * @license
   * Copyright 2019 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */const n='[DEFAULT]';
/**
   * @license
   * Copyright 2019 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */class s{constructor(e,t){this.name=e,this.container=t,this.component=null,this.instances=new Map,this.instancesDeferred=new Map,this.instancesOptions=new Map,this.onInitCallbacks=new Map}get(t){const n=this.normalizeInstanceIdentifier(t);if(!this.instancesDeferred.has(n)){const t=new e.Deferred;if(this.instancesDeferred.set(n,t),this.isInitialized(n)||this.shouldAutoInitialize())try{const e=this.getOrInitializeService({instanceIdentifier:n});e&&t.resolve(e)}catch(e){}}return this.instancesDeferred.get(n).promise}getImmediate(e){const t=this.normalizeInstanceIdentifier(e?.identifier),n=e?.optional??!1;if(!this.isInitialized(t)&&!this.shouldAutoInitialize()){if(n)return null;throw Error(`Service ${this.name} is not available`)}try{return this.getOrInitializeService({instanceIdentifier:t})}catch(e){if(n)return null;throw e}}getComponent(){return this.component}setComponent(e){if(e.name!==this.name)throw Error(`Mismatching Component ${e.name} for Provider ${this.name}.`);if(this.component)throw Error(`Component for ${this.name} has already been provided`);if(this.component=e,this.shouldAutoInitialize()){if(o(e))try{this.getOrInitializeService({instanceIdentifier:n})}catch(e){}for(const[e,t]of this.instancesDeferred.entries()){const n=this.normalizeInstanceIdentifier(e);try{const e=this.getOrInitializeService({instanceIdentifier:n});t.resolve(e)}catch(e){}}}}clearInstance(e=n){this.instancesDeferred.delete(e),this.instancesOptions.delete(e),this.instances.delete(e)}async delete(){const e=Array.from(this.instances.values());await Promise.all([...e.filter(e=>'INTERNAL'in e).map(e=>e.INTERNAL.delete()),...e.filter(e=>'_delete'in e).map(e=>e._delete())])}isComponentSet(){return null!=this.component}isInitialized(e=n){return this.instances.has(e)}getOptions(e=n){return this.instancesOptions.get(e)||{}}initialize(e={}){const{options:t={}}=e,n=this.normalizeInstanceIdentifier(e.instanceIdentifier);if(this.isInitialized(n))throw Error(`${this.name}(${n}) has already been initialized`);if(!this.isComponentSet())throw Error(`Component ${this.name} has not been registered yet`);const s=this.getOrInitializeService({instanceIdentifier:n,options:t});for(const[e,t]of this.instancesDeferred.entries()){n===this.normalizeInstanceIdentifier(e)&&t.resolve(s)}return s}onInit(e,t){const n=this.normalizeInstanceIdentifier(t),s=this.onInitCallbacks.get(n)??new Set;s.add(e),this.onInitCallbacks.set(n,s);const o=this.instances.get(n);return o&&e(o,n),()=>{s.delete(e)}}invokeOnInitCallbacks(e,t){const n=this.onInitCallbacks.get(t);if(n)for(const s of n)try{s(e,t)}catch{}}getOrInitializeService({instanceIdentifier:e,options:t={}}){let s=this.instances.get(e);if(!s&&this.component&&(s=this.component.instanceFactory(this.container,{instanceIdentifier:(o=e,o===n?void 0:o),options:t}),this.instances.set(e,s),this.instancesOptions.set(e,t),this.invokeOnInitCallbacks(s,e),this.component.onInstanceCreated))try{this.component.onInstanceCreated(this.container,e,s)}catch{}var o;return s||null}normalizeInstanceIdentifier(e=n){return this.component?this.component.multipleInstances?e:n:e}shouldAutoInitialize(){return!!this.component&&"EXPLICIT"!==this.component.instantiationMode}}function o(e){return"EAGER"===e.instantiationMode}
/**
   * @license
   * Copyright 2019 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */class c{constructor(e){this.name=e,this.providers=new Map}addComponent(e){const t=this.getProvider(e.name);if(t.isComponentSet())throw new Error(`Component ${e.name} has already been registered with ${this.name}`);t.setComponent(e)}addOrOverwriteComponent(e){this.getProvider(e.name).isComponentSet()&&this.providers.delete(e.name),this.addComponent(e)}getProvider(e){if(this.providers.has(e))return this.providers.get(e);const t=new s(e,this);return this.providers.set(e,t),t}getProviders(){return Array.from(this.providers.values())}}},1768,[1766]);
__d(function(g,r,i,a,m,e,d){"use strict";Object.defineProperty(e,'__esModule',{value:!0}),Object.defineProperty(e,"unwrap",{enumerable:!0,get:function(){return n.u}}),Object.defineProperty(e,"wrap",{enumerable:!0,get:function(){return n.w}}),Object.defineProperty(e,"deleteDB",{enumerable:!0,get:function(){return o}}),Object.defineProperty(e,"openDB",{enumerable:!0,get:function(){return t}});var n=r(d[0]);function t(t,o,{blocked:s,upgrade:c,blocking:u,terminated:l}={}){const f=indexedDB.open(t,o),b=(0,n.w)(f);return c&&f.addEventListener('upgradeneeded',t=>{c((0,n.w)(f.result),t.oldVersion,t.newVersion,(0,n.w)(f.transaction),t)}),s&&f.addEventListener('blocked',n=>s(n.oldVersion,n.newVersion,n)),b.then(n=>{l&&n.addEventListener('close',()=>l()),u&&n.addEventListener('versionchange',n=>u(n.oldVersion,n.newVersion,n))}).catch(()=>{}),b}function o(t,{blocked:o}={}){const s=indexedDB.deleteDatabase(t);return o&&s.addEventListener('blocked',n=>o(n.oldVersion,n)),(0,n.w)(s).then(()=>{})}const s=['get','getKey','getAll','getAllKeys','count'],c=['put','add','delete','clear'],u=new Map;function l(n,t){if(!(n instanceof IDBDatabase)||t in n||'string'!=typeof t)return;if(u.get(t))return u.get(t);const o=t.replace(/FromIndex$/,''),l=t!==o,f=c.includes(o);if(!(o in(l?IDBIndex:IDBObjectStore).prototype)||!f&&!s.includes(o))return;const b=async function(n,...t){const s=this.transaction(n,f?'readwrite':'readonly');let c=s.store;return l&&(c=c.index(t.shift())),(await Promise.all([c[o](...t),f&&s.done]))[0]};return u.set(t,b),b}(0,n.r)(n=>Object.assign({},n,{get:(t,o,s)=>l(t,o)||n.get(t,o,s),has:(t,o)=>!!l(t,o)||n.has(t,o)}))},1837,[1839]);
__d(function(g,r,i,a,m,e,d){"use strict";Object.defineProperty(e,'__esModule',{value:!0}),Object.defineProperty(e,"getDefaultsFromPostinstall",{enumerable:!0,get:function(){return t}});
/**
   * @license
   * Copyright 2025 Google LLC
   *
   * Licensed under the Apache License, Version 2.0 (the "License");
   * you may not use this file except in compliance with the License.
   * You may obtain a copy of the License at
   *
   *   http://www.apache.org/licenses/LICENSE-2.0
   *
   * Unless required by applicable law or agreed to in writing, software
   * distributed under the License is distributed on an "AS IS" BASIS,
   * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   * See the License for the specific language governing permissions and
   * limitations under the License.
   */
const t=()=>{}},1838,[]);
__d(function(g,r,i,a,m,e,d){"use strict";Object.defineProperty(e,'__esModule',{value:!0}),Object.defineProperty(e,"a",{enumerable:!0,get:function(){return p}}),Object.defineProperty(e,"i",{enumerable:!0,get:function(){return t}}),Object.defineProperty(e,"r",{enumerable:!0,get:function(){return l}}),Object.defineProperty(e,"u",{enumerable:!0,get:function(){return B}}),Object.defineProperty(e,"w",{enumerable:!0,get:function(){return I}});const t=(t,n)=>n.some(n=>t instanceof n);let n,o;const s=new WeakMap,c=new WeakMap,u=new WeakMap,f=new WeakMap,p=new WeakMap;function b(t){const n=new Promise((n,o)=>{const s=()=>{t.removeEventListener('success',c),t.removeEventListener('error',u)},c=()=>{n(I(t.result)),s()},u=()=>{o(t.error),s()};t.addEventListener('success',c),t.addEventListener('error',u)});return n.then(n=>{n instanceof IDBCursor&&s.set(n,t)}).catch(()=>{}),p.set(n,t),n}function v(t){if(c.has(t))return;const n=new Promise((n,o)=>{const s=()=>{t.removeEventListener('complete',c),t.removeEventListener('error',u),t.removeEventListener('abort',u)},c=()=>{n(),s()},u=()=>{o(t.error||new DOMException('AbortError','AbortError')),s()};t.addEventListener('complete',c),t.addEventListener('error',u),t.addEventListener('abort',u)});c.set(t,n)}let D={get(t,n,o){if(t instanceof IDBTransaction){if('done'===n)return c.get(t);if('objectStoreNames'===n)return t.objectStoreNames||u.get(t);if('store'===n)return o.objectStoreNames[1]?void 0:o.objectStore(o.objectStoreNames[0])}return I(t[n])},set:(t,n,o)=>(t[n]=o,!0),has:(t,n)=>t instanceof IDBTransaction&&('done'===n||'store'===n)||n in t};function l(t){D=t(D)}function y(c){return'function'==typeof c?(f=c)!==IDBDatabase.prototype.transaction||'objectStoreNames'in IDBTransaction.prototype?(o||(o=[IDBCursor.prototype.advance,IDBCursor.prototype.continue,IDBCursor.prototype.continuePrimaryKey])).includes(f)?function(...t){return f.apply(B(this),t),I(s.get(this))}:function(...t){return I(f.apply(B(this),t))}:function(t,...n){const o=f.call(B(this),t,...n);return u.set(o,t.sort?t.sort():[t]),I(o)}:(c instanceof IDBTransaction&&v(c),t(c,n||(n=[IDBDatabase,IDBObjectStore,IDBIndex,IDBCursor,IDBTransaction]))?new Proxy(c,D):c);var f}function I(t){if(t instanceof IDBRequest)return b(t);if(f.has(t))return f.get(t);const n=y(t);return n!==t&&(f.set(t,n),p.set(n,t)),n}const B=t=>p.get(t)},1839,[]);