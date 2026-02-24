-- Materialized mart: network edges for Tableau
DROP TABLE IF EXISTS mart_network_edges;
CREATE TABLE mart_network_edges AS
SELECT source, target, edge_type, weight
FROM graph_edges;
