/******************************************************************************
This source code is licensed under the MIT license found in the
LICENSE file in the root directory of this source tree.
*******************************************************************************/

#include <iostream>
#include <tacos/collective/all_gather.h>
#include <tacos/event-queue/timer.h>
#include <tacos/synthesizer/synthesizer.h>
#include <tacos/topology/mesh_2d.h>
#include <tacos/topology/sm_bi_2d.h>
#include <tacos/topology/partial_sm_bi_2d.h>
#include <tacos/topology/sm_uni_2d.h>
#include <tacos/topology/sm_uni_2d_rs.h>
#include <tacos/topology/sm_alter_even_2d.h>
#include <tacos/topology/partial_sm_alter_even_2d.h>
#include <tacos/topology/sm_alter_odd_2d.h>
#include <tacos/topology/folded_torus.h>
#include <tacos/topology/butterfly.h>
#include <tacos/topology/cmesh.h>
#include <tacos/topology/kite.h>
#include <tacos/topology/kite_medium.h>
#include <tacos/writer/csv_writer.h>
#include <tacos/writer/synthesis_result.h>

using namespace tacos;

int main() {
    // set print precision
    fixed(std::cout);
    std::cout.precision(2);

    // print header
    std::cout << "[TACOS]" << std::endl;
    std::cout << std::endl;

//    std::vector<int> v = {3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16};
//    std::vector<int> v = {4, 6, 8, 10, 12, 14, 16};
    std::vector<int> v = {8};
    for(int i=0; i<v.size(); i++){
        // construct a topology
        const auto width = v[i];
        const auto height = v[i];
//        const auto bandwidth = 200.0;  // GB/s
//        const auto latency = 0;  // ns
        std::string topology_name = "folded_torus";
        int total_nodes = width * height;
        // Here low means lower length link and high means higher length links
        const auto bandwidth_low = 100.0;  // GB/s
        const auto latency_low = 0;     // ns
        const auto bandwidth_high = 66.0;  // GB/s
        const auto latency_high = 0;     // ns

//        const auto topology = std::make_shared<Mesh2D>(width, height, latency, bandwidth);
//        const auto topology = std::make_shared<SM_Bi_2D>(width, height, latency, bandwidth);
//        const auto topology = std::make_shared<SM_Alter_Odd_2D>(width, height, latency, bandwidth);
//        const auto topology = std::make_shared<SM_Alter_Even_2D>(width, height, latency, bandwidth);
//        const auto topology = std::make_shared<SM_Uni_2D>(width, height, latency, bandwidth);
//        const auto topology = std::make_shared<SM_Uni_2D_RS>(width, height, latency, bandwidth);
        const auto topology = std::make_shared<FoldedTorus>(width, height, latency_high, bandwidth_high, latency_low, bandwidth_low);
//        const auto topology = std::make_shared<Butterfly>(width, height, latency, bandwidth);
//        const auto topology = std::make_shared<CMesh>(width, height, latency, bandwidth);
//        const auto topology = std::make_shared<Kite>(width, height, latency, bandwidth);
//        const auto topology = std::make_shared<KiteMedium>(width, height, latency, bandwidth);
//        const auto topology = std::make_shared<Partial_SM_Bi_2D>(width, height, latency, bandwidth);
//        const auto topology = std::make_shared<Partial_SM_Alter_Even_2D>(width, height, latency, bandwidth);
        const auto npusCount = topology->getNpusCount();

        std::cout << "[Topology Information]" << std::endl;
        std::cout << "\t- NPUs Count: " << npusCount << std::endl;
        std::cout << std::endl;

        // target collective
        const auto chunkSize = 1'048'576;  // B
        const auto initChunksPerNpu = 4;

        const auto collective = std::make_shared<AllGather>(npusCount, chunkSize, initChunksPerNpu);
        const auto chunksCount = collective->getChunksCount();

        std::cout << "[Collective Information]" << std::endl;
        const auto chunkSizeMB = chunkSize / (1 << 20);
        std::cout << "\t- Chunks Count: " << chunksCount << std::endl;
        std::cout << "\t- Chunk Size: " << chunkSize << " B";
        std::cout << " (" << chunkSizeMB << " MB)" << std::endl;
        std::cout << std::endl;

        // instantiate synthesizer
        auto synthesizer = Synthesizer(topology, collective, total_nodes, topology_name, true);

        // create timer
        auto timer = Timer();

        // synthesize collective algorithm
        std::cout << "[Synthesis Process]" << std::endl;

        timer.start();
        const auto synthesisResult = synthesizer.synthesize();
        timer.stop();

        std::cout << std::endl;

        // print result
        std::cout << "[Synthesis Result]" << std::endl;

        const auto elapsedTimeUSec = timer.elapsedTime();
        const auto elapsedTimeSec = elapsedTimeUSec / 1e6;
        std::cout << "\t- Time to solve: " << elapsedTimeUSec << " us";
        std::cout << " (" << elapsedTimeSec << " s)" << std::endl;

        const auto collectiveTimePS = synthesisResult.getCollectiveTime();
        const auto collectiveTimeUSec = collectiveTimePS / 1.0e6;
        std::cout << "\t- Synthesized Collective Time: " << collectiveTimePS << " ps";
        std::cout << " (" << collectiveTimeUSec << " us)" << std::endl;
        std::cout << std::endl;

        // write results to file
        std::cout << "[Synthesis Result Dump]" << std::endl;
        const auto csvWriter = CsvWriter(topology, collective, synthesisResult);
        std::string csvFilename = "tacos_" + std::to_string(total_nodes) + "_" + std::string(topology_name) + ".csv";
        csvWriter.write(csvFilename);

        std::cout << std::endl;
    }

    // terminate
    std::cout << "[TACOS] Done!" << std::endl;
    return 0;
}
