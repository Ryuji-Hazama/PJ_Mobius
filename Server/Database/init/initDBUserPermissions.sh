set -e
until mysqladmin ping -h "localhost" --silent; do
    sleep 1
done

mysql -u root -p$MYSQL_ROOT_PASSWORD <<-EOSQL

    REVOKE ALL PRIVILEGES ON *.* FROM 'mobius'@'%';
    GRANT INSERT, UPDATE, SELECT, DELETE ON MobiusDB.ComputerLanguageTypes TO 'mobius'@'%';
    GRANT INSERT, UPDATE, SELECT, DELETE ON MobiusDB.ComputerLanguages TO 'mobius'@'%';
    GRANT INSERT, UPDATE, SELECT, DELETE ON MobiusDB.ContractCompanies TO 'mobius'@'%';
    GRANT INSERT, UPDATE, SELECT, DELETE ON MobiusDB.Contracts TO 'mobius'@'%';
    GRANT INSERT, UPDATE, SELECT, DELETE ON MobiusDB.Employees TO 'mobius'@'%';
    GRANT INSERT, UPDATE, SELECT, DELETE ON MobiusDB.Projects TO 'mobius'@'%';
    GRANT INSERT, UPDATE, SELECT, DELETE ON MobiusDB.Users TO 'mobius'@'%';
    GRANT INSERT, UPDATE, SELECT ON MobiusDB.SessionInfo TO 'mobius'@'%';
    GRANT SELECT ON MobiusDB.ContractLevel TO 'mobius'@'%';
    REVOKE ALL PRIVILEGES ON *.* FROM 'root'@'%';
    GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost';

    FLUSH PRIVILEGES;
EOSQL