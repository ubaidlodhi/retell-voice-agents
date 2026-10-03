const norm = (s) => (s || '').toString().toLowerCase().replace(/[^a-z]/g, '');
const aliases = { mercedes: 'mercedesbenz', benz: 'mercedesbenz', mercedesbenz: 'mercedesbenz', vw: 'volkswagen', volkswagon: 'volkswagen', chevy: 'chevrolet' };
const makeKey = aliases[norm(dv.vehicle_make)] || norm(dv.vehicle_make);
const possess = (dv.in_possession || '').toString().toLowerCase().trim() !== 'false';
// Purchase vs lease (script Q2): this call's answer first, else the value on file in GHL (seeded by the pre-call).
const ptOf = (v) => { const t = norm(v); if (!t || t === 'na') return ''; if (t === 'leasebuyout' || t.indexOf('leasedthenpurchased') === 0 || t.indexOf('buyout') !== -1) return 'lease_buyout'; if (t.indexOf('lease') === 0) return 'leased'; if (t.indexOf('purchase') === 0 || t === 'bought') return 'purchased'; return ''; };
const pt = ptOf(dv.purchase_type_call) || ptOf(dv.purchase_type);
const optedIn = ['alfaromeo','buick','cadillac','chevrolet','chrysler','dodge','fiat','ford','gmc','hummer','infiniti','jaguar','jeep','kia','landrover','lincoln','maserati','mercedesbenz','mercury','mitsubishi','nissan','pontiac','ram','saturn','smart','hyundai','subaru','genesis','vinfast'];
const retainerMakes = ['acura','buick','cadillac','gmc','chevrolet','ford','lincoln','hyundai','kia','nissan','infiniti','volkswagen','jeep','ram','dodge','chrysler','bmw','mercedesbenz','jaguar','landrover','mazda','audi'];
const leaseArbitration = ['honda','acura','bmw','mercedesbenz','mini'];
const buyoutArbitration = ['honda','acura'];
const buyoutNonRetainer = ['bmw','mercedesbenz','mini'];
if (!makeKey) { return { route: 'reprompt', bad_reason: 'N/A', lead_status: '' }; }
if (pt === 'leased' && leaseArbitration.includes(makeKey)) { return { route: 'bad', bad_reason: 'arbitration_lease', lead_status: 'Bad Lead' }; }
if (pt === 'lease_buyout' && buyoutArbitration.includes(makeKey)) { return { route: 'bad', bad_reason: 'arbitration_buyout', lead_status: 'Bad Lead' }; }
if (!possess && optedIn.includes(makeKey)) { return { route: 'bad', bad_reason: 'not_in_possession', lead_status: 'Bad Lead' }; }
const year = parseInt(dv.vehicle_year, 10);
if (!year || isNaN(year)) { return { route: 'reprompt', bad_reason: 'N/A', lead_status: '' }; }
if (year <= 2020) { return { route: 'bad', bad_reason: 'vehicle_year', lead_status: 'Bad Lead' }; }
if (pt === 'lease_buyout' && buyoutNonRetainer.includes(makeKey)) { return { route: 'non_retainer', bad_reason: 'N/A', lead_status: 'Non-Retainer Lead' }; }
if (makeKey === 'tesla') { return { route: 'bad', bad_reason: 'arbitration_tesla', lead_status: 'Bad Lead' }; }
if (retainerMakes.includes(makeKey)) { return { route: 'retainer', bad_reason: 'N/A', lead_status: 'Retainer Pending' }; }
return { route: 'non_retainer', bad_reason: 'N/A', lead_status: 'Non-Retainer Lead' };
