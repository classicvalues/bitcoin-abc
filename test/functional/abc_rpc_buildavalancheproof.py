#!/usr/bin/env python3
# Copyright (c) 2021 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test the buildavalancheproof RPC"""

from test_framework.avatools import create_coinbase_stakes
from test_framework.key import ECKey
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import (
    assert_raises_rpc_error,
)


class BuildAvalancheProofTest(BitcoinTestFramework):
    def set_test_params(self):
        self.num_nodes = 1
        self.extra_args = [['-enableavalanche=1', '-avacooldown=0']]

    def run_test(self):
        node = self.nodes[0]

        addrkey0 = node.get_deterministic_priv_key()
        blockhashes = node.generatetoaddress(2, addrkey0.address)
        stakes = create_coinbase_stakes(node, [blockhashes[0]], addrkey0.key)

        privkey = ECKey()
        privkey.generate()

        proof_master = privkey.get_pubkey().get_bytes().hex()

        def check_buildavalancheproof_error(
                error_code, error_message, stakes):
            assert_raises_rpc_error(
                error_code,
                error_message,
                node.buildavalancheproof,
                # Sequence
                0,
                # Expiration
                0,
                # Master
                proof_master,
                stakes,
            )

        good_stake = stakes[0]

        self.log.info("Error cases")

        negative_vout = good_stake.copy()
        negative_vout['vout'] = -1
        check_buildavalancheproof_error(-22,
                                        "vout must be positive",
                                        [negative_vout],
                                        )

        zero_height = good_stake.copy()
        zero_height['height'] = 0
        check_buildavalancheproof_error(-22,
                                        "height must be positive",
                                        [zero_height],
                                        )
        negative_height = good_stake.copy()
        negative_height['height'] = -1
        check_buildavalancheproof_error(-22,
                                        "height must be positive",
                                        [negative_height],
                                        )

        missing_amount = good_stake.copy()
        del missing_amount['amount']
        check_buildavalancheproof_error(-8,
                                        "Missing amount",
                                        [missing_amount],
                                        )

        invalid_privkey = good_stake.copy()
        invalid_privkey['privatekey'] = 'foobar'
        check_buildavalancheproof_error(-8,
                                        "Invalid private key",
                                        [invalid_privkey],
                                        )

        self.log.info("Happy path")
        assert node.buildavalancheproof(0, 0, proof_master, [good_stake])


if __name__ == '__main__':
    BuildAvalancheProofTest().main()
