SELECT
    'EZ24' as evenementcode,
	s.bedrijf,
	c.naam,
	es.aangebracht_door,
	es.bedrag_kaarten,
	es.netto_bedrag_excl_btw,
	es.facturatie_bedrag_incl_btw,
	es.gefactureerd,
	es.betaald,
	es.opmerkingen
FROM tmp_event_sponsor es
JOIN tmp_sponsor s ON es.sponsor_id = s.sponsor_id
JOIN tmp_contract c ON es.contract_id = c.contract_id
