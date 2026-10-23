from fakes import ethereum, wikidata

from omega_grounding.evidence import Verdict
from omega_grounding.nal import parse
from omega_grounding.sources.evm import MAINNET_TOKENS, PROXY_SLOTS, SELECTOR_DECIMALS, SELECTOR_SYMBOL, EvmSource
from omega_grounding.sources.wikidata import WikidataSource

LABELS = {
    "dolphin": [("Q1", "Dolphin", "label"), ("Q7369", "dolphin", "label")],  # Q1: a surname
    "mammal": [("Q7377", "mammal", "label")],
    "whale": [("Q20", "whale", "label")],
    "fish": [("Q152", "fish", "label")],
    "violin": [("Q8355", "violin", "label")],
    "string instrument": [("Q1798603", "string instrument", "label")],
}
LINKS = {
    "Q1": {"P31": ["Q101352"]},
    "Q7369": {"P279": ["Q215760"]},          # common-name item -> Delphinidae
    "Q215760": {"P171": ["Q7377"]},          # taxon -> Mammalia
    "Q7377": {"P171": ["Q99"]},
    "Q20": {"P279": ["Q160"]},               # whale -> Cetacea
    "Q160": {"P171": ["Q7377"], "P279": ["Q152"]},  # a clade-mixing subclass link to fish
    "Q8355": {"P279": ["Q1798603"]},
}


def source(closed_world=True):
    return WikidataSource(wikidata(LABELS, LINKS), closed_world=closed_world)


def test_wikidata_supports_through_taxon_tree_and_skips_surname_sense():
    ev = source().check(parse("(--> dolphin mammal)"))
    assert ev.verdict is Verdict.SUPPORTS
    assert "Q7369" in ev.provenance


def test_wikidata_detects_relation_swap():
    ev = source().check(parse("(--> mammal dolphin)"))
    assert ev.verdict is Verdict.REFUTES
    assert ev.correction == parse("(--> dolphin mammal)")


def test_wikidata_taxa_follow_parent_taxon_only():
    # Cetacea's subclass link to fish must not make whales fish
    ev = source().check(parse("(--> whale fish)"))
    assert ev.verdict is Verdict.REFUTES and ev.correction is None


def test_wikidata_open_world_returns_unknown():
    ev = source(closed_world=False).check(parse("(--> whale fish)"))
    assert ev.verdict is Verdict.UNKNOWN


def test_wikidata_non_taxon_classes_use_subclass_links():
    assert source().check(parse("(--> violin string_instrument)")).verdict is Verdict.SUPPORTS


def test_wikidata_unresolved_term_is_unknown():
    assert source().check(parse("(--> dolphin unicorn)")).verdict is Verdict.UNKNOWN


def test_wikidata_supports_only_plain_inheritance():
    s = source()
    assert s.supports(parse("(--> dolphin mammal)"))
    assert not s.supports(parse("(--> (× usdc 6) decimals)"))
    assert not s.supports(parse("(<-> dolphin porpoise)"))


USDC = MAINNET_TOKENS["usdc"]
WETH = MAINNET_TOKENS["weth"]
EOA = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"


def word(n):
    return "0x" + format(n, "064x")


def abi_string(s):
    data = s.encode()
    return "0x" + format(32, "064x") + format(len(data), "064x") + data.hex().ljust(64, "0")


def evm():
    return EvmSource(ethereum(
        code={USDC: "0x6080", WETH: "0x6060", EOA: "0xef0100" + "11" * 20},
        storage={(USDC, PROXY_SLOTS["OpenZeppelin legacy implementation"]): word(0xABC)},
        calls={(USDC, SELECTOR_DECIMALS): word(6), (WETH, SELECTOR_SYMBOL): abi_string("WETH")},
    ))


def test_evm_decimals_correction():
    ev = evm().check(parse("(--> (× usdc 18) decimals)"))
    assert ev.verdict is Verdict.REFUTES
    assert ev.correction == parse("(--> (× usdc 6) decimals)")
    assert evm().check(parse("(--> (× usdc 6) decimals)")).verdict is Verdict.SUPPORTS


def test_evm_proxy_detection():
    assert evm().check(parse("(--> usdc ([] upgradeable))")).verdict is Verdict.SUPPORTS
    ev = evm().check(parse("(--> weth ([] upgradeable))"))
    assert ev.verdict is Verdict.REFUTES and ev.truth.c == 0.8


def test_evm_delegated_eoa_is_not_a_contract():
    ev = evm().check(parse(f"(--> {EOA} ([] contract))"))
    assert ev.verdict is Verdict.REFUTES and "7702" in ev.provenance


def test_evm_symbol_is_case_insensitive():
    assert evm().check(parse("(--> (× weth weth) symbol)")).verdict is Verdict.SUPPORTS


def test_evm_ignores_unknown_tokens():
    assert not evm().supports(parse("(--> (× notarealtoken 18) decimals)"))


def test_evm_accepts_natural_phrasings():
    from omega_grounding.sources.evm import canonical_form

    assert canonical_form(parse("(--> usdc smart_contract)")) == parse("(--> usdc ([] contract))")
    assert canonical_form(parse("(--> usdt_token upgradeable_proxy)")) == parse("(--> usdt ([] upgradeable))")
    assert canonical_form(parse("(--> (× uni_token_contract 18) decimal_places)")) == parse("(--> (× uni 18) decimals)")
    assert canonical_form(parse("(--> dolphin mammal)")) is None
    assert evm().check(parse("(--> usdc smart_contract)")).verdict is Verdict.SUPPORTS
    assert evm().check(parse("(--> weth upgradeable_proxy)")).verdict is Verdict.REFUTES


def test_evm_accepts_value_inside_predicate():
    from omega_grounding.sources.evm import canonical_form

    usdc = MAINNET_TOKENS["usdc"]
    assert canonical_form(parse("(--> usdc (decimals 6))")) == parse("(--> (× usdc 6) decimals)")
    assert canonical_form(parse(f"(--> (× usdc {usdc}) (decimals 18))")) == parse("(--> (× usdc 18) decimals)")
    ev = evm().check(parse(f"(--> (× usdc {usdc}) (decimals 18))"))
    assert ev.verdict is Verdict.REFUTES and ev.correction == parse("(--> (× usdc 6) decimals)")


def test_unknown_lists_the_shapes_sources_accept():
    from omega_grounding.grounder import Grounder

    ev = Grounder([evm()]).evidence(parse("(--> schuman-europ erc20-eur-stablecoin)"))
    assert ev.verdict is Verdict.UNKNOWN and "(--> (× TOKEN N) decimals)" in ev.provenance
