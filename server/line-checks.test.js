const { test } = require('node:test');
const assert = require('node:assert/strict');
const { lineKey, applyChecks } = require('./line-checks');
const now = Date.now();
const row = { id:'1', sport:'NFL', player:'Player', stat:'rushing yards', line:63.5, start_time:new Date(now+3600000).toISOString(), prizepicks_observed_at:new Date(now).toISOString() };
test('known mismatch follows the event/stat even after source line moves', () => {
 const checks = {[lineKey(row)]: {actual_line:62.5,variant:'standard',checked_at:new Date(now).toISOString()}};
 assert.equal(applyChecks([row], checks, now).quarantined.length, 1);
 assert.equal(applyChecks([{...row,line:59.5}], checks, now).accepted.length, 0);
 const accepted = applyChecks([{...row,line:62.5}], checks, now).accepted;
 assert.equal(accepted[0].line_status, 'user_confirmed');
 assert.equal(applyChecks([{...row,line:62.5}], checks, now+900001).quarantined.length,1);
});
test('modifier cannot qualify for standard model and no observation claims verification', () => {
 assert.equal(applyChecks([row],{},now).accepted[0].line_status,'unverified');
 assert.equal(applyChecks([row],{[lineKey(row)]:{actual_line:63.5,variant:'goblin',checked_at:new Date(now).toISOString()}},now).quarantined.length,1);
});
