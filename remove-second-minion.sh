#!/usr/bin/env bash
echo "This script will remove a salt2-minion from your workstation"
echo "Do you wish to remove this program?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) sudo salt-call --local --log-level=info state.apply remove_second_minion; break;;
        No ) exit;;
    esac
done

