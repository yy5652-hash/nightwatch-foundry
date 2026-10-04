/* Tablekeeper's browser trusts accepted API responses, never cached success. */
(() => {
  'use strict';
  const main = document.querySelector('#main');
  const header = document.querySelector('#site-header');
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const test = id => document.querySelector(`[data-testid="${id}"]`);
  const tablesOf = reservation => Array.isArray(reservation.table_ids) ? reservation.table_ids : [reservation.table_id];
  const labelOf = (restaurant, id) => {
    const label = restaurant?.tables?.find(t => t.id === id)?.label;
    return label == null ? 'Table' : /^\d+$/.test(label) ? `Table ${label}` : label;
  };
  const labelsOf = (restaurant, ids) => ids.map(id => labelOf(restaurant, id)).join(' + ');
  const friendlyDate = value => new Intl.DateTimeFormat('en-GB', {weekday:'short',day:'numeric',month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(value+'T12:00:00Z'));
  const friendlyLocal = value => `${friendlyDate(value.slice(0,10))} · ${value.slice(11,16)}`;
  // Historic wire offsets may be minute-aligned representations of an exact
  // instant. Immutable older records can also contain offset seconds. Neither
  // wire clock is necessarily the restaurant's wall clock.
  const friendlyInstant = (value, zone) => {
    const match=/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|([+-])(\d{2}):(\d{2})(?::(\d{2}))?)$/.exec(value);
    if(!match || !zone)return 'Local end time unavailable';
    const clock=new Date(0);
    clock.setUTCFullYear(Number(match[1]),Number(match[2])-1,Number(match[3]));
    clock.setUTCHours(Number(match[4]),Number(match[5]),Number(match[6]),Number((match[7]||'').padEnd(3,'0').slice(0,3)));
    const offset=match[8]==='Z'?0:(match[9]==='+'?1:-1)*(Number(match[10])*3600+Number(match[11])*60+Number(match[12]||0));
    const instant=new Date(clock.getTime()-offset*1000);
    try {
      const format=new Intl.DateTimeFormat('en-GB',{weekday:'short',day:'numeric',month:'long',year:'numeric',hour:'2-digit',minute:'2-digit',hourCycle:'h23',timeZone:zone});
      const parts=Object.fromEntries(format.formatToParts(instant).map(part=>[part.type,part.value]));
      return `${parts.weekday}, ${parts.day} ${parts.month} ${parts.year} · ${parts.hour}:${parts.minute}`;
    } catch (_) { return 'Local end time unavailable'; }
  };
  const today = () => {
    const date = new Date();
    return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
  };
  const readSession = () => {
    try {
      const value = JSON.parse(sessionStorage.getItem('tablekeeper.session'));
      return value && typeof value.token === 'string' && typeof value.display_name === 'string' ? value : null;
    } catch (_) { return null; }
  };
  const state = {
    route: location.pathname, user: readSession(), authEpoch: 0,
    restaurants: [], cataloguePhase: 'loading', catalogueError: '',
    query: {restaurantId:'', date:today(), party:'2'}, searchSeq:0,
    result:null, searchPhase:'idle', searchError:'', authError:'',
    booking:null, afterLogin:null,
    lookup:{reference:'', phase:'idle', detail:null, restaurant:null, error:'', seq:0,
      decision:null, history:null, series:null, seriesError:'', recurrence:null},
    seriesByReference:new Map(),
  };
  class Refusal extends Error {
    constructor(status, value) { super(value?.error?.message || 'The request could not be accepted.'); this.status=status; this.code=value?.error?.code; }
  }
  const refusalText = (error, context) => ({
    email_taken:'An account already uses this email address. Sign in instead.',
    unauthenticated:context==='auth'?'The email address or password was not recognised. Please check them and try again.':'Please sign in again to continue.',
    cutoff_passed:'This reservation is too close to its start time to cancel or change.',
    party_exceeds_capacity:'This seating option cannot accommodate that many guests. Choose a larger table or an approved pair.',
    invalid_local_time:'This local time does not exist because the clocks change. Choose another available time.',
    outside_opening_hours:'This time falls outside the restaurant’s booking hours. Choose an available time.',
    not_on_slot_grid:'Choose one of the restaurant’s available start times.',
    validation_failed:context==='auth'?'Please check your email and account details. New passwords need at least 8 characters.':'Please check the date, seating choice and number of guests.',
    reservation_cancelled:'This reservation has already been cancelled.',
    already_in_series:'This reservation already belongs to a recurring agreement. Use its agreement reference to load the current occurrences.',
    stale_revision:'This reservation changed while you were viewing it. Refresh its details before trying again.',
  }[error.code] || error.message);
  function parseAPIJSON(raw) {
    // Validate syntax first: quoting a large numeric token must never turn an
    // invalid document (such as an unquoted numeric key) into a valid response.
    JSON.parse(raw);
    const number=/-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/y;
    const safe=BigInt(Number.MAX_SAFE_INTEGER);
    // Whole numeric values can arrive with a decimal point or exponent. Resolve
    // their coefficient and scale exactly before selecting a display value.
    const integerValue=token=>{
      const match=/^(-?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$/.exec(token);
      let digits=(match[2]+(match[3]||'')).replace(/^0+/,'');
      if(!digits)return '0';
      const shift=BigInt(match[4]||'0')-BigInt((match[3]||'').length);
      if(shift<0n) {
        const remove=-shift;
        if(remove>=BigInt(digits.length))return null;
        const count=Number(remove);
        if(!/^0+$/.test(digits.slice(-count)))return null;
        digits=digits.slice(0,-count);
      } else digits+='0'.repeat(Number(shift));
      return match[1]+digits;
    };
    let exact='',index=0;
    while(index<raw.length) {
      if(raw[index]==='"') {
        const start=index++;
        while(index<raw.length) {
          if(raw[index]==='\\')index+=2;
          else if(raw[index++]==='"')break;
        }
        exact+=raw.slice(start,index);
      } else if(raw[index]==='-' || /[0-9]/.test(raw[index])) {
        number.lastIndex=index;const match=number.exec(raw);
        if(!match){exact+=raw[index++];continue;}
        const token=match[0];
        const integer=integerValue(token);
        if(integer!==null && (BigInt(integer)>safe || BigInt(integer)<-safe))exact+=JSON.stringify(integer);
        else exact+=token;
        index=number.lastIndex;
      } else exact+=raw[index++];
    }
    return JSON.parse(exact);
  }
  async function api(path, {method='GET', body, rawBody, key, token=state.user?.token}={}) {
    const headers = {Accept:'application/json'};
    if (token) headers.Authorization = `Bearer ${token}`;
    if (key) headers['Idempotency-Key'] = key;
    if (body !== undefined || rawBody !== undefined) headers['Content-Type']='application/json; charset=utf-8';
    const response = await fetch(path, {method, headers, body:rawBody ?? (body === undefined ? undefined : JSON.stringify(body)), cache:'no-store'});
    let value;
    if (response.status !== 204) {
      try { value = parseAPIJSON(await response.text()); }
      catch (_) { throw new Error('The connection ended before a complete response arrived.'); }
    }
    if (!response.ok) {
      if (response.status >= 500) throw new Error('The service could not confirm the outcome.');
      throw new Refusal(response.status, value);
    }
    return value;
  }
  function rememberUser(user) {
    state.user=user;
    state.authEpoch++;
    state.seriesByReference.clear();
    try { if (user) sessionStorage.setItem('tablekeeper.session', JSON.stringify(user)); else sessionStorage.removeItem('tablekeeper.session'); } catch (_) {}
  }
  const feedback = (id, message, kind='error') => message ? `<div data-testid="${id}" class="feedback ${kind}" role="${kind==='error'?'alert':'status'}">${esc(message)}</div>` : '';
  function guestNumber(id, testid, value) {
    return `<div class="number-control"><button type="button" data-step="-1" tabindex="-1" aria-label="One fewer guest">−</button><input id="${id}" data-testid="${testid}" type="text" inputmode="numeric" role="spinbutton" aria-valuemin="1" value="${esc(value)}" autocomplete="off" spellcheck="false" required><button type="button" data-step="1" tabindex="-1" aria-label="One more guest">+</button></div>`;
  }
  function bindGuestNumber(input) {
    const container=input.closest('.number-control');
    const update=()=>{
      const value=decimal(input.value);
      if(value)input.setAttribute('aria-valuenow',value);else input.removeAttribute('aria-valuenow');
      input.setAttribute('aria-valuetext',value?`${value} guests`:'Enter a whole number of guests');
      container.querySelector('[data-step="-1"]').disabled=value==='1';
    };
    const step=direction=>{
      const next=BigInt(decimal(input.value)||'1')+BigInt(direction);
      input.value=(next<1n?1n:next).toString();
      input.dispatchEvent(new Event('input',{bubbles:true}));input.focus();
    };
    input.addEventListener('input',update);
    input.addEventListener('keydown',event=>{if(event.key==='ArrowUp'||event.key==='ArrowDown'){event.preventDefault();step(event.key==='ArrowUp'?1:-1);}});
    container.querySelectorAll('[data-step]').forEach(button=>button.addEventListener('click',()=>step(button.dataset.step)));
    update();
  }
  const links = '<p class="muted">Already have an account? <a href="/login" data-route>Sign in</a>. New here? <a href="/signup" data-route>Create an account</a>.</p>';
  function renderHeader() {
    header.innerHTML=`<a href="/" data-route class="brand" aria-label="Tablekeeper home"><span class="brand-mark" aria-hidden="true">t</span><span>Tablekeeper<small>A place at the table</small></span></a>
      <nav aria-label="Main navigation"><a href="/" data-route ${state.route==='/'?'aria-current="page"':''}>Find a table</a><a href="/lookup" data-route ${state.route==='/lookup'?'aria-current="page"':''}>Your reservation</a></nav>
      <div class="account">${state.user ? `<span data-testid="current-user">${esc(state.user.display_name)}</span><button class="button secondary compact" data-testid="logout-button" type="button">Sign out</button>` : '<a href="/login" data-route>Sign in</a><a class="button secondary compact" href="/signup" data-route>Create account</a>'}</div>`;
    test('logout-button')?.addEventListener('click', () => {
      rememberUser(null); state.booking=null; state.afterLogin=null; state.authError='';
      state.lookup.seq++; state.lookup.detail=null; state.lookup.restaurant=null; state.lookup.phase='idle'; state.lookup.error='';
      state.lookup.decision=null;state.lookup.history=null;state.lookup.series=null;state.lookup.recurrence=null;state.lookup.seriesError='';render();
    });
  }
  function navigate(route, replace=false) {
    if (!['/','/signup','/login','/lookup'].includes(route)) return;
    if (replace) history.replaceState(null,'',route); else if (route!==location.pathname) history.pushState(null,'',route);
    state.route=route; state.authError=''; render();
    main.focus();
  }
  document.addEventListener('click', event => {
    const anchor=event.target.closest('a[data-route]');
    if (!anchor || event.button!==0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault(); navigate(new URL(anchor.href).pathname);
  });
  addEventListener('popstate', () => { state.route=location.pathname; state.authError=''; render(); });
  function render() {
    renderHeader();
    if (state.route==='/signup' || state.route==='/login') renderAuth();
    else if (state.route==='/lookup') renderLookup();
    else renderSearch();
  }
  function renderAuth() {
    const signup=state.route==='/signup', prefix=signup?'signup':'login';
    document.title=`${signup?'Create account':'Sign in'} · Tablekeeper`;
    main.innerHTML=`<div class="auth-layout"><section class="auth-intro"><p class="eyebrow">${signup?'Make yourself at home':'Welcome back'}</p><h1>${signup?'Good company.<br>A table waiting.':'Your next meal<br>starts here.'}</h1><p class="lead">${signup?'Create an account to book a table and keep your reservation close at hand.':'Sign in to book, look up a reservation, or make room for your next visit.'}</p><div class="quiet-note">Browse restaurants and available times before signing in. Your selection will be here when you return.</div></section><section class="auth-card"><h2>${signup?'Create your account':'Sign in'}</h2>
      ${state.user?`<p class="feedback success">You are signed in as ${esc(state.user.display_name)}.</p><a href="/" data-route class="button">Find a table</a>`:`<form id="auth-form" novalidate>
        ${signup?'<label for="display-name">Your name</label><input id="display-name" data-testid="signup-display-name" name="display_name" autocomplete="name" required>':''}
        <label for="auth-email">Email address</label><input id="auth-email" data-testid="${prefix}-email" name="email" type="email" autocomplete="email" required>
        <label for="auth-password">Password</label><input id="auth-password" data-testid="${prefix}-password" name="password" type="password" autocomplete="${signup?'new-password':'current-password'}" required>${signup?'<p class="input-hint">Use at least 8 characters.</p>':''}
        <div id="auth-feedback">${feedback('auth-error',state.authError)}</div><button data-testid="${prefix}-submit" class="button full" type="submit">${signup?'Create account':'Sign in'}</button></form>${links}`}
      </section></div>`;
    document.querySelector('#auth-form')?.addEventListener('submit', async event => {
      event.preventDefault(); const form=event.currentTarget, button=test(`${prefix}-submit`);
      const fields=new FormData(form); const body={email:fields.get('email'), password:fields.get('password')};
      if (signup) body.display_name=fields.get('display_name');
      button.disabled=true; button.textContent=signup?'Creating account…':'Signing in…';
      document.querySelector('#auth-feedback').innerHTML='';
      try {
        const user=await api(`/auth/${prefix}`,{method:'POST',body,token:null});
        if (!user || typeof user.token!=='string' || typeof user.display_name!=='string') throw new Error('Sign in could not be confirmed.');
        rememberUser(user); state.authError='';
        if (state.afterLogin) { state.booking=state.afterLogin; state.afterLogin=null; }
        navigate('/');
      } catch (error) {
        if (state.route!==`/${prefix}`) return;
        state.authError=error instanceof Refusal ? refusalText(error,'auth') : 'Unable to connect. Please try again.';
        document.querySelector('#auth-feedback').innerHTML=feedback('auth-error',state.authError);
        button.disabled=false; button.textContent=signup?'Create account':'Sign in';
      }
    });
  }
  function renderSearch() {
    document.title='Find a table · Tablekeeper';
    const q=state.query;
    main.innerHTML=`<section class="hero"><div><p class="eyebrow">Time together, well spent</p><h1>Find your place<br>at the table.</h1><p class="lead">Choose a restaurant, a time, and a seat that suits your company.</p></div><p class="hero-note">Your table.<br>Your kind of evening.</p></section>
      <section class="search-card" aria-label="Find availability"><form id="search-form" class="search-fields" novalidate>
        <div><label for="restaurant">Restaurant</label><select id="restaurant" data-testid="restaurant-select" ${state.cataloguePhase==='loading'?'disabled':''}>${state.restaurants.length?state.restaurants.map(r=>`<option value="${esc(r.id)}" ${r.id===q.restaurantId?'selected':''}>${esc(r.name)}</option>`).join(''):'<option value="">'+(state.cataloguePhase==='loading'?'Loading restaurants…':'No restaurants available')+'</option>'}</select></div>
        <div><label for="visit-date">Date</label><input id="visit-date" data-testid="date-input" type="date" value="${esc(q.date)}" required></div>
        <div><label for="search-party">Guests</label>${guestNumber('search-party','party-size-input',q.party)}</div>
        <button type="submit" class="button" data-testid="search-button" ${!state.restaurants.length?'disabled':''}>Find a table</button>
      </form><div id="search-feedback"></div></section><div class="results-layout"><section class="results-panel" id="results-panel" aria-live="polite"></section><aside id="booking-panel"></aside></div>`;
    ['restaurant-select','date-input','party-size-input'].forEach(id=>test(id).addEventListener('input', () => {
      const next={restaurantId:test('restaurant-select').value,date:test('date-input').value,party:test('party-size-input').value};
      if (JSON.stringify(next)!==JSON.stringify(state.query)) {
        state.query=next; state.searchSeq++; state.searchPhase='idle'; state.searchError=''; state.result=null; state.booking=null; state.afterLogin=null; state.authError='';
        renderResults(); renderBooking();
      }
    }));
    bindGuestNumber(test('party-size-input'));
    document.querySelector('#search-form').addEventListener('submit', event=>{event.preventDefault(); search();});
    renderResults(); renderBooking();
  }
  function renderResults() {
    const panel=document.querySelector('#results-panel'); if (!panel) return;
    document.querySelector('#search-feedback').innerHTML=state.catalogueError?feedback('search-error',state.catalogueError):feedback('search-error',state.searchError);
    if (state.cataloguePhase==='loading' || state.searchPhase==='loading') {
      panel.innerHTML='<div class="empty-state"><span class="loading-dot" aria-hidden="true"></span><h2>Finding a place for you</h2><p class="muted">Checking tables and local opening times…</p></div>'; return;
    }
    if (state.cataloguePhase==='error') { panel.innerHTML='<div class="empty-state"><h2>We couldn’t load the restaurants</h2><p class="muted">Please try the connection again.</p><button id="catalogue-retry" class="button secondary">Try again</button></div>'; document.querySelector('#catalogue-retry').onclick=loadCatalogue; return; }
    if (!state.restaurants.length) { panel.innerHTML='<div class="empty-state"><h2>No restaurants to browse yet</h2><p class="muted">Check back when restaurant details have been added.</p></div>';return; }
    if (!state.result) { panel.innerHTML=`<div class="empty-state"><p class="eyebrow">A little planning, a lovely meal</p><h2>${state.searchError?'Try another search':'Where shall we meet?'}</h2><p class="muted">Choose your date and party size, then find a table.</p></div>`;return; }
    const {restaurant,availability,query}=state.result;
    let top=`<div class="results-heading"><div><p class="eyebrow">${esc(restaurant.name)}</p><h2>${esc(friendlyDate(query.date))}</h2><p class="muted">${esc(query.party)} ${query.party==='1'?'guest':'guests'} · Times in ${esc(restaurant.timezone)}</p></div><span class="availability-key"><span></span>Available</span></div>${feedback('auth-error',state.authError)}`;
    if (!availability.slots.length) { panel.innerHTML=top+'<div data-testid="no-slots" class="empty-state"><h3>No times on this date</h3><p class="muted">This restaurant has no booking slots for the selected day. Try another date.</p></div>';return; }
    top+='<div data-testid="availability-grid" class="availability-grid">';
    availability.slots.forEach((slot,slotIndex)=>{
      top+=`<div class="slot-row"><div class="slot-heading"><strong>${esc(slot.starts_at_local.slice(11))}</strong><span>Local time</span></div><div class="seat-options">`;
      const cell=(ids,available,combination=false)=>{
        const selected=state.booking && state.booking.starts===slot.starts_at_local && JSON.stringify(state.booking.ids)===JSON.stringify(ids);
        const option=slot.available_options?.find(option=>JSON.stringify(option.table_ids)===JSON.stringify(ids));
        const capacity=option?.capacity ?? (!slot.explain?ids.reduce((n,id)=>n+BigInt(restaurant.tables.find(t=>t.id===id).capacity),0n).toString():null);
        const reasons=ids.flatMap(id=>(slot.explain?.find(item=>item.table_id===id)?.rules||[]).filter(rule=>!rule.holds).map(rule=>rule.rule==='capacity'?'Too few seats':'Already booked'));
        const description=available?'Choose table':reasons.length?[...new Set(reasons)].join(' · '):'Unavailable';
        return `<button type="button" class="seat ${combination?'combination ':''}${selected?'selected':''}" data-testid="slot-${esc(ids.join('+'))}-${esc(slot.starts_at_local.slice(11))}" data-available="${available}" data-slot="${slotIndex}" data-tables="${esc(JSON.stringify(ids))}" ${available?'':'disabled'} aria-pressed="${!!selected}"><strong>${esc(labelsOf(restaurant,ids))}</strong><span>${combination?'Together · ':''}${capacity===null?'':esc(capacity)+' seats · '}${esc(description)}</span></button>`;
      };
      restaurant.tables.forEach(table=>{top+=cell([table.id],slot.available_table_ids.includes(table.id));});
      (slot.available_options || []).filter(option=>option.table_ids.length===2).forEach(option=>{top+=cell(option.table_ids,true,true);});
      top+='</div></div>';
    });
    panel.innerHTML=top+'</div><p class="input-hint">Availability is checked again when you book. Combined tables are offered only as approved pairs.</p>';
    panel.querySelectorAll('button[data-available="true"]').forEach(button=>button.addEventListener('click',()=>{
      const booking={restaurant,ids:JSON.parse(button.dataset.tables),starts:availability.slots[Number(button.dataset.slot)].starts_at_local,party:query.party,identity:null,phase:'idle',error:'',uncertain:'',confirmation:null,changedNotice:''};
      if (!state.user) { state.authError='Sign in to book this table. Your selection will be kept for you.';state.afterLogin=booking;renderResults();return; }
      state.booking=booking; state.authError=''; renderResults();renderBooking();test('booking-party-size')?.focus();
    }));
  }
  function decimal(raw) {
    if (!/^[0-9]+$/.test(raw)) return null;
    const value=BigInt(raw); return value>0n?value.toString():null;
  }
  async function search(preserveBooking=false) {
    const seq=++state.searchSeq, query={...state.query}, party=decimal(query.party);
    state.searchError='';
    if (!query.restaurantId || !/^\d{4}-\d{2}-\d{2}$/.test(query.date) || !party) {
      state.searchPhase='error';state.searchError='Choose a restaurant, a date, and a whole number of guests greater than zero.';renderResults();return;
    }
    query.party=party;state.searchPhase='loading';if (!preserveBooking) { state.booking=null;state.afterLogin=null; }
    renderResults();renderBooking();
    try {
      const [restaurant,availability]=await Promise.all([
        api(`/restaurants/${encodeURIComponent(query.restaurantId)}`),
        api(`/availability?restaurant_id=${encodeURIComponent(query.restaurantId)}&date=${encodeURIComponent(query.date)}&party_size=${encodeURIComponent(party)}&explain=true`)
      ]);
      if (seq!==state.searchSeq) return;
      state.result={restaurant,availability,query};state.searchPhase='ready';state.authError='';renderResults();renderBooking();
    } catch (error) {
      if (seq!==state.searchSeq) return;
      state.searchPhase='error';state.result=null;state.searchError=error instanceof Refusal?refusalText(error,'search'):'Availability could not be loaded. Please try again.';renderResults();renderBooking();
    }
  }
  function bookingBody(booking) {
    const party=decimal(booking.party); if (!party) return null;
    const selection=booking.ids.length===1?`"table_id":${JSON.stringify(booking.ids[0])}`:`"table_ids":${JSON.stringify(booking.ids)}`;
    return `{"restaurant_id":${JSON.stringify(booking.restaurant.id)},${selection},"starts_at_local":${JSON.stringify(booking.starts)},"party_size":${party}}`;
  }
  function requestIdentity(booking) {
    const rawBody=bookingBody(booking); if (!rawBody) return null;
    if (!booking.identity || booking.identity.rawBody!==rawBody) {
      const random=new Uint8Array(16);crypto.getRandomValues(random);
      booking.identity={rawBody,key:'tk-'+Array.from(random,v=>v.toString(16).padStart(2,'0')).join('')};
    }
    return booking.identity;
  }
  function renderBooking() {
    const panel=document.querySelector('#booking-panel');if (!panel) return;
    const b=state.booking;
    if (!b) {panel.innerHTML='<div class="booking-placeholder"><span class="place-symbol" aria-hidden="true">✦</span><h3>A seat for your occasion</h3><p>Choose an available table to see your booking details here.</p>'+(!state.user?'<a href="/login" data-route>Sign in to book</a>':'')+'</div>';return;}
    panel.innerHTML=`<section data-testid="booking-form" class="booking-card"><p class="eyebrow">Your table</p><h2>${esc(b.restaurant.name)}</h2><p data-testid="booking-summary" class="booking-summary">${esc(labelsOf(b.restaurant,b.ids))}<br><time datetime="${esc(b.starts)}">${esc(friendlyLocal(b.starts))}</time></p><p class="input-hint">${esc(b.restaurant.timezone)} · Booking terms are confirmed with your reservation.</p><form id="booking-fields" novalidate><fieldset ${b.phase==='submitting'?'disabled':''}><label for="booking-guests">Guests</label>${guestNumber('booking-guests','booking-party-size',b.party)}<div id="booking-feedback"></div><button class="button full" data-testid="booking-submit" type="submit">${b.phase==='submitting'?'Confirming…':b.uncertain?'Retry this booking':b.confirmation?'Check confirmation again':'Confirm booking'}</button></fieldset></form><div id="booking-confirmation"></div><p class="input-hint">A reference appears only after the restaurant service confirms your booking.</p></section>`;
    renderBookingFeedback();renderConfirmation();
    test('booking-party-size').addEventListener('input',event=>{
      const oldBody=bookingBody(b);b.party=event.target.value;
      if (bookingBody(b)!==oldBody) {
        b.changedNotice=b.uncertain?'Your previous attempt may have booked a table. Changing these details starts a separate booking request.':'';
        b.identity=null;b.error='';b.uncertain='';b.confirmation=null;b.phase='idle';renderBookingFeedback();renderConfirmation();
        test('booking-submit').textContent='Confirm booking';
      }
    });
    bindGuestNumber(test('booking-party-size'));
    document.querySelector('#booking-fields').addEventListener('submit',event=>{event.preventDefault();submitBooking(b);});
  }
  function renderBookingFeedback() {
    const panel=document.querySelector('#booking-feedback');if(!panel || !state.booking)return;
    const b=state.booking;panel.innerHTML=feedback('booking-error',b.error)+feedback('booking-uncertain',b.uncertain,'uncertain')+(b.changedNotice?`<p class="feedback uncertain">${esc(b.changedNotice)}</p>`:'');
  }
  function renderConfirmation() {
    const panel=document.querySelector('#booking-confirmation'); if (!panel)return;
    const b=state.booking,r=b?.confirmation;
    panel.innerHTML=r?`<section data-testid="confirmation" class="confirmation" role="status"><p class="eyebrow">Original booking confirmation</p><p class="input-hint">Booking reference</p><p data-testid="confirmation-reference" class="reference">${esc(r.reference)}</p><p data-testid="confirmation-details">${esc(b.restaurant.name)}<br>${esc(labelsOf(b.restaurant,tablesOf(r)))}<br><time datetime="${esc(r.starts_at_local)}">${esc(friendlyLocal(r.starts_at_local))}</time></p><p data-testid="confirmation-tables">${esc(labelsOf(b.restaurant,tablesOf(r)))}</p><div data-testid="confirmation-terms">${r.accepted_terms?termsMarkup(r.accepted_terms,b.restaurant,'Terms accepted for this booking'):'<p class="input-hint">This original receipt predates booking terms. Look up the current reservation for its details.</p>'}</div>${r.revision?`<p class="input-hint">Original booking revision ${esc(r.revision)}</p>`:''}<a href="/lookup" data-route data-open-reference="${esc(r.reference)}">View current details, history or recurring visits</a></section>`:'';
    panel.querySelector('[data-open-reference]')?.addEventListener('click',event=>{clearLookupExtras();state.lookup.reference=event.currentTarget.dataset.openReference;state.lookup.detail=null;state.lookup.phase='idle';state.lookup.error='';});
  }
  async function submitBooking(b) {
    if (b.phase==='submitting' || state.booking!==b) return;
    if (!state.user) {b.error='Sign in before confirming a booking.';renderBooking();return;}
    const identity=requestIdentity(b);
    if (!identity) {b.error='Enter a whole number of guests greater than zero.';b.uncertain='';b.confirmation=null;renderBooking();return;}
    const epoch=state.authEpoch;b.phase='submitting';b.error='';b.uncertain='';b.confirmation=null;b.changedNotice='';renderBooking();
    try {
      const receipt=await api('/reservations',{method:'POST',rawBody:identity.rawBody,key:identity.key});
      if (state.booking!==b || state.authEpoch!==epoch) return;
      if (!receipt || typeof receipt.reference!=='string' || !/^[A-Z0-9]{6,12}$/.test(receipt.reference)) throw new Error('Booking confirmation was incomplete.');
      b.confirmation=receipt;b.phase='confirmed';b.error='';b.uncertain='';renderBooking();
    } catch (error) {
      if (state.booking!==b || state.authEpoch!==epoch) return;
      b.phase='idle';b.confirmation=null;
      if (error instanceof Refusal) {
        b.error=error.code==='table_unavailable'?'This table was just taken. We’ve refreshed availability; your details are kept below. Choose another option to continue.':refusalText(error,'booking');
        b.uncertain='';renderBooking();
        if (error.code==='table_unavailable') await search(true);
      } else { b.error='';b.uncertain='We couldn’t confirm the response. Your booking may have succeeded. Retry this unchanged form to recover its original reference.';renderBooking(); }
    }
  }
  function renderLookup() {
    document.title='Your reservation · Tablekeeper';
    const l=state.lookup;
    main.innerHTML=`<section class="hero compact-hero"><div><p class="eyebrow">Plans, close at hand</p><h1>Your reservation.</h1><p class="lead">Use your booking reference to find the details or cancel your table.</p></div></section><div class="lookup-layout"><section class="lookup-card"><h2>Find your booking</h2><form id="lookup-form" novalidate><label for="reference">Booking reference</label><input id="reference" data-testid="lookup-reference-input" value="${esc(l.reference)}" autocomplete="off" autocapitalize="characters" spellcheck="false"><p class="input-hint">Enter the reference exactly as shown on your confirmation.</p><button data-testid="lookup-submit" class="button full" ${l.phase==='loading'?'disabled':''}>${l.phase==='loading'?'Finding reservation…':'Find reservation'}</button></form>${!state.user?'<p class="quiet-note">Sign in to see your own reservations.</p>'+links:''}<div id="lookup-feedback"></div></section><section id="reservation-panel"></section></div>`;
    renderLookupDetail();
    test('lookup-reference-input').addEventListener('input',event=>{clearLookupExtras();l.reference=event.target.value;l.seq++;l.detail=null;l.error='';l.phase='idle';test('lookup-submit').disabled=false;test('lookup-submit').textContent='Find reservation';renderLookupDetail();});
    document.querySelector('#lookup-form').addEventListener('submit',event=>{event.preventDefault();lookup();});
  }
  function renderLookupDetail() {
    const panel=document.querySelector('#reservation-panel'),feedbackPanel=document.querySelector('#lookup-feedback');if(!panel)return;
    const l=state.lookup,r=l.detail;
    feedbackPanel.innerHTML=feedback('reservation-error',l.error);
    if (!r) {panel.innerHTML=`<div class="booking-placeholder"><span class="place-symbol" aria-hidden="true">✦</span><h3>${l.phase==='loading'?'Finding your reservation':'A reference to your plans'}</h3><p>${l.phase==='loading'?'Checking the details with the restaurant…':'Your restaurant, table and time will appear here.'}</p></div>`;return;}
    panel.innerHTML=`<section data-testid="reservation-detail" class="lookup-card"><div class="detail-heading"><p class="eyebrow">${esc(l.restaurant?.name || 'Your reservation')}</p><span data-testid="reservation-status" class="status ${r.status==='cancelled'?'cancelled':''}">${esc(r.status)}</span></div><h2><time datetime="${esc(r.starts_at_local)}">${esc(friendlyLocal(r.starts_at_local))}</time></h2><p data-testid="reservation-tables" class="booking-summary">${esc(labelsOf(l.restaurant,tablesOf(r)))}</p><dl class="detail-list"><div><dt>Guests</dt><dd>${esc(r.party_size)}</dd></div><div><dt>Booking reference</dt><dd class="reference small">${esc(r.reference)}</dd></div><div><dt>Local time zone</dt><dd>${esc(l.restaurant?.timezone || '')}</dd></div><div><dt>Ends at</dt><dd><time datetime="${esc(r.ends_at)}">${esc(friendlyInstant(r.ends_at,l.restaurant?.timezone))}</time></dd></div></dl>${r.status==='confirmed'?`<p class="input-hint">Your accepted cancellation cutoff is ${esc(r.accepted_terms?.cancellation_cutoff_minutes ?? l.restaurant?.cancellation_cutoff_minutes ?? '')} minutes before this start.</p><button type="button" data-testid="reservation-cancel-button" class="button secondary full" ${l.phase==='cancelling'?'disabled':''}>${l.phase==='cancelling'?'Cancelling…':'Cancel reservation'}</button>`:'<p class="feedback success">This reservation is cancelled. The table has been released.</p>'}<div data-testid="reservation-current-terms">${l.decision?`<p data-testid="reservation-revision" class="revision-note">Current revision ${esc(l.decision.revision)}</p>${termsMarkup(l.decision.accepted_terms,l.restaurant,'Your accepted booking terms')}`:'<p class="input-hint">Accepted-term details are unavailable from this service.</p>'}</div></section>${historyMarkup()}<section id="series-panel"></section>`;
    test('reservation-cancel-button')?.addEventListener('click',cancelReservation);
    renderSeries();
  }
  function clearLookupExtras() {
    const l=state.lookup;l.seq++;l.decision=null;l.history=null;l.series=null;
    l.seriesError='';l.seriesPhase='idle';l.seriesQuery='';l.seriesSeq=(l.seriesSeq||0)+1;l.recurrence=null;
  }
  function termsMarkup(terms,restaurant,title) {
    if(!terms)return '';
    const days={mon:'Monday',tue:'Tuesday',wed:'Wednesday',thu:'Thursday',fri:'Friday',sat:'Saturday',sun:'Sunday'};
    return `<details class="terms-block"><summary>${esc(title)} · policy ${esc(terms.policy_version)}</summary><dl class="detail-list"><div><dt>Duration</dt><dd>${esc(terms.reservation_duration_minutes)} minutes</dd></div><div><dt>Cancellation cutoff</dt><dd>${esc(terms.cancellation_cutoff_minutes)} minutes before the start</dd></div><div><dt>Start-time grid</dt><dd>Every ${esc(terms.slot_minutes)} minutes from opening</dd></div></dl><h4>Accepted opening hours</h4><ul>${(terms.opening_hours||[]).map(day=>`<li>${esc(days[day.weekday]||day.weekday)} · ${esc(day.opens)}–${esc(day.closes)}</li>`).join('')||'<li>Closed every day</li>'}</ul><h4>Accepted table capacities</h4><ul>${Object.entries(terms.capacities||{}).map(([id,capacity])=>`<li>${esc(labelOf(restaurant,id))} · ${esc(capacity)} seats</li>`).join('')}</ul><p class="input-hint">These are the terms accepted for this reservation. Later published policies do not rewrite them.</p></details>`;
  }
  function historyMarkup() {
    const l=state.lookup;
    if(!l.history)return '<section class="lookup-card history-card"><h3>Your booking history</h3><p class="input-hint">History is unavailable from this service.</p></section>';
    const fieldNames={table_id:'Table',table_ids:'Tables',starts_at_local:'Local start',party_size:'Guests'};
    const value=(field,v)=>v===null?'Not previously booked':field==='table_ids'?labelsOf(l.restaurant,v):field==='table_id'?labelOf(l.restaurant,v):field==='starts_at_local'?friendlyLocal(v):String(v);
    return `<section data-testid="reservation-history" class="lookup-card history-card"><p class="eyebrow">Your plans, as they changed</p><h3>Booking history</h3><ol class="history-list">${l.history.entries.map(entry=>`<li data-testid="history-entry-${esc(entry.seq)}"><div class="history-heading"><strong>${esc({created:'Booked',changed:'Changed',cancelled:'Cancelled'}[entry.event]||entry.event)}</strong><span>Revision ${esc(entry.revision)} · event ${esc(entry.seq)}</span></div><time datetime="${esc(entry.at)}">${esc(friendlyInstant(entry.at,l.restaurant?.timezone))}</time>${entry.changes.length?`<ul>${entry.changes.map(change=>`<li><strong>${esc(fieldNames[change.field]||change.field)}</strong>: ${esc(value(change.field,change.from))} → ${esc(value(change.field,change.to))}</li>`).join('')}</ul>`:'<p class="input-hint">No booking fields changed in this event.</p>'}${termsMarkup(entry.accepted_terms,l.restaurant,'Terms at this event')}</li>`).join('')}</ol></section>`;
  }
  async function optionalOwnerRead(path) {
    try{return await api(path);}catch(error){if(error instanceof Refusal&&error.status===404)return null;throw error;}
  }
  async function loadCurrentDetails(reference) {
    const path=`/reservations/${encodeURIComponent(reference)}`;
    const receipt=await api(path);
    const [restaurant,decision,entries]=await Promise.all([
      api(`/restaurants/${encodeURIComponent(receipt.restaurant_id)}`),
      optionalOwnerRead(path+'/decision'),optionalOwnerRead(path+'/history')
    ]);
    if(decision && (String(decision.revision)!==String(receipt.revision) || entries?.entries?.at(-1)?.revision!==receipt.revision))throw new Error('The reservation changed while its details were loading. Please refresh.');
    return {receipt,restaurant,decision,history:entries};
  }
  function seriesBody(s) {
    if(!/^\d+$/.test(s.count)||!/^\d+$/.test(s.interval))return null;
    const count=Number(s.count),interval=Number(s.interval);
    if(count<2||count>12||interval<1||interval>4)return null;
    return JSON.stringify({anchor_reference:state.lookup.detail.reference,count,interval_weeks:interval});
  }
  function renderSeries() {
    const panel=document.querySelector('#series-panel'),l=state.lookup,r=l.detail;
    if(!panel||!r||!l.decision)return;
    if(!l.recurrence)l.recurrence={count:'4',interval:'1',identity:null,phase:'idle',error:'',uncertain:'',original:null,notice:''};
    const s=l.recurrence,known=state.seriesByReference.get(r.reference);
    const occurrences=l.series?.occurrences;
    panel.innerHTML=`<section class="lookup-card series-card"><p class="eyebrow">Make it a regular occasion</p><h3>Recurring visits</h3>${r.status==='confirmed'&&(!known||s.identity)?`<p>Keep this reservation as your first visit. Each later date is checked against its own booking terms and availability.</p><form data-testid="series-form" id="series-form" novalidate><fieldset ${s.phase==='submitting'?'disabled':''}><div class="series-fields"><div><label for="series-count">Total visits, including this one</label><input id="series-count" data-testid="series-count" type="number" min="2" max="12" step="1" value="${esc(s.count)}"></div><div><label for="series-interval">Weeks between visits</label><input id="series-interval" data-testid="series-interval-weeks" type="number" min="1" max="4" step="1" value="${esc(s.interval)}"></div></div><button data-testid="series-submit" class="button full">${s.phase==='submitting'?'Checking every visit…':s.uncertain?'Retry this recurring request':s.original?'Check original agreement again':'Arrange recurring visits'}</button></fieldset></form>`:known?'<p>This reservation belongs to a recurring agreement. Its references stay the same when an individual visit changes.</p>':'<p class="input-hint">A cancelled reservation cannot start a recurring agreement.</p>'}${feedback('series-error',s.error)}${feedback('series-uncertain',s.uncertain,'uncertain')}${s.notice?`<p class="feedback uncertain">${esc(s.notice)}</p>`:''}${s.original?`<div data-testid="series-confirmation" class="feedback success">The recurring request was confirmed.<br>Agreement reference: <span data-testid="series-id" class="reference small">${esc(s.original.series_id)}</span><p class="input-hint">This is the original successful request. The list below loads the agreement’s current states.</p></div>`:''}<form id="series-load-form" class="series-load"><label for="series-lookup-id">Agreement reference</label><input id="series-lookup-id" data-testid="series-lookup-id" value="${esc(l.seriesQuery||known||l.series?.series_id||'')}" autocomplete="off"><button class="button secondary full" data-testid="series-refresh" ${l.seriesPhase==='loading'?'disabled':''}>${l.seriesPhase==='loading'?'Loading current visits…':'Load current visits'}</button></form>${feedback('series-load-error',l.seriesError)}${occurrences?`<div data-testid="series-occurrences"><div class="history-heading"><h4>Current visits</h4><span data-testid="series-revision">Agreement revision ${esc(l.series.revision)}</span></div><ol class="occurrence-list">${occurrences.map(item=>`<li data-testid="series-occurrence-${esc(item.index)}"><div class="history-heading"><strong>Visit ${esc(Number(item.index)+1)}</strong><span class="status ${item.reservation.status==='cancelled'?'cancelled':''}">${esc(item.reservation.status)}</span></div><p>${esc(friendlyLocal(item.reservation.starts_at_local))}<br>${esc(labelsOf(l.restaurant,tablesOf(item.reservation)))}</p><p class="input-hint">${item.exception?'Individual change · permanent exception':'Part of the recurring agreement'}</p><button type="button" data-occurrence-reference="${esc(item.reference)}" class="button secondary compact">View ${esc(item.reference)}</button></li>`).join('')}</ol><p class="input-hint">Cancelling one visit keeps its siblings. An individually changed visit remains an exception.</p></div>`:l.seriesPhase==='loading'?'<p class="quiet-note" role="status">Checking the current occurrence list…</p>':''}</section>`;
    panel.querySelector('#series-form')?.addEventListener('submit',event=>{event.preventDefault();submitSeries(s);});
    [['series-count','count'],['series-interval-weeks','interval']].forEach(([id,key])=>test(id)?.addEventListener('input',event=>{
      const old=seriesBody(s);s[key]=event.target.value;
      if(seriesBody(s)!==old){s.notice=s.uncertain?'The previous request may have succeeded. Changing these values starts a separate request.':'';s.identity=null;s.phase='idle';s.error='';s.uncertain='';s.original=null;['series-error','series-uncertain','series-confirmation'].forEach(id=>test(id)?.remove());panel.querySelector('#series-changed-notice')?.remove();if(s.notice)panel.querySelector('#series-form').insertAdjacentHTML('afterend',`<p id="series-changed-notice" class="feedback uncertain">${esc(s.notice)}</p>`);test('series-submit').textContent='Arrange recurring visits';}
    }));
    test('series-lookup-id').addEventListener('input',event=>{l.seriesQuery=event.target.value;l.seriesSeq=(l.seriesSeq||0)+1;l.series=null;l.seriesPhase='idle';l.seriesError='';test('series-occurrences')?.remove();test('series-load-error')?.remove();test('series-refresh').disabled=false;test('series-refresh').textContent='Load current visits';});
    panel.querySelector('#series-load-form').addEventListener('submit',event=>{event.preventDefault();refreshSeries(test('series-lookup-id').value,l.seq,state.authEpoch);});
    panel.querySelectorAll('[data-occurrence-reference]').forEach(button=>button.addEventListener('click',()=>{clearLookupExtras();l.reference=button.dataset.occurrenceReference;lookup();}));
  }
  async function refreshSeries(id,seq,epoch) {
    const l=state.lookup,loadSeq=l.seriesSeq=(l.seriesSeq||0)+1;l.seriesQuery=id;l.series=null;l.seriesError='';
    if(!id){l.seriesError='Enter the agreement reference issued by the service.';renderSeries();return;}
    l.seriesPhase='loading';renderSeries();
    try {
      const current=await api(`/series/${encodeURIComponent(id)}`);
      if(seq!==l.seq||epoch!==state.authEpoch||loadSeq!==l.seriesSeq)return;
      if(current.series_id!==id||!Array.isArray(current.occurrences))throw new Error('Incomplete recurring response');
      const member=current.occurrences.find(item=>item.reference===l.detail?.reference);
      if(member&&JSON.stringify(member.reservation)!==JSON.stringify(l.detail)){
        const details=await loadCurrentDetails(member.reference);
        if(seq!==l.seq||epoch!==state.authEpoch||loadSeq!==l.seriesSeq)return;
        l.detail=details.receipt;l.decision=details.decision;l.history=details.history;
      }
      l.series=current;l.seriesPhase='ready';current.occurrences.forEach(item=>state.seriesByReference.set(item.reference,id));renderLookupDetail();
    }catch(error){if(seq!==l.seq||epoch!==state.authEpoch||loadSeq!==l.seriesSeq)return;l.seriesPhase='idle';l.seriesError=error instanceof Refusal&&error.status===404?'No recurring agreement was found for this account and reference.':error instanceof Refusal?refusalText(error,'series'):'Current visits could not be loaded. Please retry.';renderSeries();}
  }
  async function submitSeries(s) {
    const l=state.lookup;if(l.recurrence!==s||s.phase==='submitting')return;
    const body=seriesBody(s);
    if(!body){s.error='Choose 2 to 12 total visits and an interval of 1 to 4 weeks.';s.uncertain='';renderSeries();return;}
    if(!s.identity||s.identity.rawBody!==body){const random=new Uint8Array(16);crypto.getRandomValues(random);s.identity={rawBody:body,key:'tk-series-'+Array.from(random,v=>v.toString(16).padStart(2,'0')).join('')};}
    const seq=l.seq,epoch=state.authEpoch;s.phase='submitting';s.error='';s.uncertain='';s.original=null;s.notice='';l.series=null;renderSeries();
    try {
      const original=await api('/series',{method:'POST',rawBody:s.identity.rawBody,key:s.identity.key});
      if(seq!==l.seq||epoch!==state.authEpoch||l.recurrence!==s)return;
      if(typeof original?.series_id!=='string'||!Array.isArray(original.occurrences))throw new Error('Incomplete recurring confirmation');
      s.original=original;s.phase='confirmed';original.occurrences.forEach(item=>state.seriesByReference.set(item.reference,original.series_id));renderSeries();
      await refreshSeries(original.series_id,seq,epoch);
    }catch(error){if(seq!==l.seq||epoch!==state.authEpoch||l.recurrence!==s)return;s.phase='idle';s.original=null;if(error instanceof Refusal){s.error=refusalText(error,'series');s.uncertain='';}else{s.error='';s.uncertain='We could not confirm the response. Every visit may already be arranged. Retry this unchanged request to recover its original agreement.';}renderSeries();}
  }
  async function lookup() {
    const l=state.lookup,seq=++l.seq,epoch=state.authEpoch,reference=l.reference;
    l.error='';l.detail=null;
    if(!state.user || !reference) {l.error=!state.user?'Sign in to look up your own reservation.':'Enter your booking reference.';l.phase='idle';renderLookup();return;}
    l.phase='loading';renderLookup();
    try {
      const {receipt,restaurant,decision,history:entries}=await loadCurrentDetails(reference);
      if(seq!==l.seq || epoch!==state.authEpoch)return;
      l.detail=receipt;l.restaurant=restaurant;l.decision=decision;l.history=entries;l.phase='ready';renderLookup();
      const seriesId=state.seriesByReference.get(reference);
      if(seriesId)await refreshSeries(seriesId,seq,epoch);
    } catch(error) {if(seq!==l.seq || epoch!==state.authEpoch)return;l.phase='idle';l.error=error instanceof Refusal?error.status===404?'No reservation was found for this account and reference.':refusalText(error,'lookup'):'The reservation could not be loaded. Please try again.';renderLookup();}
  }
  async function cancelReservation() {
    const l=state.lookup,seq=++l.seq,epoch=state.authEpoch,reference=l.detail?.reference;
    if(!reference || l.phase==='cancelling')return;
    l.phase='cancelling';l.error='';renderLookupDetail();
    try {
      const receipt=await api(`/reservations/${encodeURIComponent(reference)}/cancel`,{method:'POST'});
      if(seq!==l.seq || epoch!==state.authEpoch)return;
      const current=await loadCurrentDetails(reference);
      if(seq!==l.seq || epoch!==state.authEpoch)return;
      l.detail=current.receipt;l.decision=current.decision;l.history=current.history;l.phase='ready';renderLookupDetail();
      const seriesId=state.seriesByReference.get(reference);if(seriesId)await refreshSeries(seriesId,seq,epoch);
    } catch(error) {if(seq!==l.seq || epoch!==state.authEpoch)return;l.phase='ready';l.error=error instanceof Refusal?refusalText(error,'cancel'):'The cancellation outcome could not be confirmed. Try again to check it.';renderLookupDetail();}
  }
  async function loadCatalogue() {
    state.cataloguePhase='loading';state.catalogueError='';render();
    try {
      const value=await api('/restaurants');state.restaurants=value.restaurants;
      if(!state.restaurants.some(r=>r.id===state.query.restaurantId))state.query.restaurantId=state.restaurants[0]?.id || '';
      state.cataloguePhase='ready';if(state.route==='/')renderSearch();
    } catch(_) {state.cataloguePhase='error';state.catalogueError='Restaurants could not be loaded. Please try again.';if(state.route==='/')renderSearch();}
  }
  render();loadCatalogue();
})();
